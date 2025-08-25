from flask import Flask, jsonify, redirect, url_for, request, session, g
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_login import current_user, logout_user
import secrets

from .models import db, User
from .routes import tasks_bp
from .config import Config
from .utils import is_ajax
from .extensions import limiter

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    Migrate(app, db)
    CSRFProtect(app)
    limiter.init_app(app)

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = None
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            user_id_int = int(user_id)
        except (TypeError, ValueError):
            return None
        return db.session.get(User, user_id_int)

    @login_manager.unauthorized_handler
    def unauthorized():
        if is_ajax():
            return jsonify({"success": False, "message": "Требуется авторизация"}), 401
        return redirect(url_for('auth.login', next=request.url))

    @app.before_request
    def generate_csp_nonce():
        # Пер-запросный nonce для CSP
        g.csp_nonce = secrets.token_urlsafe(16)

    @app.before_request
    def enforce_single_active_session():
        # Пропускаем, если пользователь не аутентифицирован
        if not getattr(current_user, 'is_authenticated', False):
            return None
        # Сверяем токен сессии из cookie c токеном в БД
        session_token = session.get('session_token')
        db_token = getattr(current_user, 'active_session_token', None)
        if not session_token or not db_token or session_token != db_token:
            # Сессия недействительна (например, выполнен вход где-то ещё) — разлогиниваем
            try:
                logout_user()
            finally:
                session.pop('session_token', None)
            if is_ajax():
                return jsonify({"success": False, "message": "Сеанс завершён: выполнен вход с другого устройства"}), 401
            return redirect(url_for('auth.login', next=request.url))
        return None

    @app.after_request
    def set_security_headers(response):
        # Базовые заголовки безопасности (щадящие по умолчанию)
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        # Доп. заголовки безопасности
        if app.config.get('ENV') == 'production':
            response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload')
        response.headers.setdefault('Permissions-Policy', 'geolocation=(), camera=(), microphone=()')

        # CSP со строгим правилом для скриптов через nonce
        csp_nonce = getattr(g, 'csp_nonce', None)
        if csp_nonce:
            csp_value = (
                "default-src 'self'; "
                "img-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; "
                f"script-src 'self' 'nonce-{csp_nonce}'; "
            )
            # Не перезаписываем, если уже задан где-то ранее
            response.headers.setdefault('Content-Security-Policy', csp_value)
        return response

    @app.context_processor
    def inject_csp_nonce():
        return {'csp_nonce': getattr(g, 'csp_nonce', '')}

    # Единые обработчики ошибок (HTML или JSON)
    def _wants_json():
        accept = request.headers.get('Accept', '')
        return is_ajax() or 'application/json' in accept

    @app.errorhandler(400)
    def handle_400(e):
        if _wants_json():
            return jsonify({"success": False, "message": "Некорректный запрос"}), 400
        return ("<h1>400</h1><p>Некорректный запрос.</p>", 400)

    @app.errorhandler(401)
    def handle_401(e):
        if _wants_json():
            return jsonify({"success": False, "message": "Требуется авторизация"}), 401
        return ("<h1>401</h1><p>Требуется авторизация.</p>", 401)

    @app.errorhandler(403)
    def handle_403(e):
        if _wants_json():
            return jsonify({"success": False, "message": "Доступ запрещён"}), 403
        return ("<h1>403</h1><p>Доступ запрещён.</p>", 403)

    @app.errorhandler(404)
    def handle_404(e):
        if _wants_json():
            return jsonify({"success": False, "message": "Страница не найдена"}), 404
        return ("<h1>404</h1><p>Страница не найдена.</p>", 404)

    @app.errorhandler(500)
    def handle_500(e):
        if _wants_json():
            return jsonify({"success": False, "message": "Внутренняя ошибка сервера"}), 500
        return ("<h1>500</h1><p>Внутренняя ошибка сервера.</p>", 500)

    # Blueprints
    from .auth import auth_bp
    from .admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tasks_bp)
    return app