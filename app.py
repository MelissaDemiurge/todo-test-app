import os
from flask import (
    Flask, render_template, request,
    session, redirect, url_for, flash
)
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, HiddenField, SubmitField
from wtforms.validators import DataRequired
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') or 'temporary_fallback'

csrf = CSRFProtect(app)


class TaskForm(FlaskForm):
    title = StringField(
        label='Название задачи',
        validators=[DataRequired(message='Нельзя добавить пустую задачу')]
    )
    submit = SubmitField('Добавить')


class MarkDoneForm(FlaskForm):
    task_index = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Отметить как выполненную')


@app.route('/', methods=['GET', 'POST'])
def index():
    task_form = TaskForm()
    mark_form = MarkDoneForm()

    session.setdefault('tasks', [])

    if task_form.validate_on_submit():
        session['tasks'].append({
            'title': task_form.title.data.strip(),
            'done': False
        })
        session.modified = True
        flash('Задача добавлена', 'success')
        return redirect(url_for('index'))

    return render_template(
        'index.html',
        tasks=session['tasks'],
        task_form=task_form,
        mark_form=mark_form
    )


@app.route('/mark_done', methods=['POST'])
def mark_done():
    form = MarkDoneForm()
    if form.validate_on_submit():
        try:
            idx = int(form.task_index.data)
            if 0 <= idx < len(session.get('tasks', [])):
                session['tasks'][idx]['done'] = True
                session.modified = True
                flash(f'Задача №{idx + 1} отмечена выполненной', 'info')
            else:
                flash('Неверный индекс задачи', 'warning')
        except ValueError:
            flash('Индекс задачи должен быть числом', 'danger')
    else:
        flash('Не удалось подтвердить действие', 'danger')

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
