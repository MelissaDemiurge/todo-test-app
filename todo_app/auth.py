from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import secrets

from .models import db, User
from .forms import LoginForm, RegisterForm
from flask import session
from .extensions import limiter


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5/minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.index'))
    form = LoginForm()
    if form.validate_on_submit():
        username_or_email = form.username.data
        password = form.password.data

        # Один параметризованный запрос: ищем либо по email, либо по username
        stmt = db.select(User).where((User.email == username_or_email) | (User.username == username_or_email))
        user = db.session.execute(stmt).scalar_one_or_none()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Неверные учетные данные', 'error')
        else:
            # Присваиваем новый токен активной сессии (атомарно)
            new_token = secrets.token_urlsafe(48)
            user.active_session_token = new_token
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                flash('Не удалось обновить сеанс. Попробуйте ещё раз', 'error')
            else:
                session.clear()
                login_user(user, remember=form.remember.data)
                session['session_token'] = new_token
                next_url = request.args.get('next')
                return redirect(next_url or url_for('tasks.index'))
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data or None
        password_hash = generate_password_hash(form.password.data)
        user = User(username=username, email=email, password_hash=password_hash)
        new_token = secrets.token_urlsafe(48)
        user.active_session_token = new_token
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.username.errors.append('Пользователь с таким именем или почтой уже существует')
        else:
            session.clear()
            login_user(user)
            session['session_token'] = new_token
            return redirect(url_for('tasks.index'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    # Сбросить токен активной сессии, чтобы немедленно инвалидировать remember-cookie
    if current_user.is_authenticated:
        current_user.active_session_token = None
        db.session.commit()
    logout_user()
    session.pop('session_token', None)
    return redirect(url_for('auth.login'))


