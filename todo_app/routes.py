from flask import Blueprint, render_template, redirect, url_for, flash, request
from todo_app.forms import TaskForm, MarkDoneForm, DeleteForm, EditForm
from todo_app.models import db, Task
from todo_app.services import get_tasks
from todo_app.utils import ajax_required  # 🔽 декоратор обработки форм

tasks_bp = Blueprint('tasks', __name__)


def get_task_by_id(id_str):
    try:
        task_id = int(id_str)
    except ValueError:
        flash('Идентификатор задачи должен быть числом', 'danger')
        return None

    task = Task.query.get(task_id)
    if task is None:
        flash('Задача с указанным ID не найдена', 'warning')
    return task


@tasks_bp.route('/', methods=['GET', 'POST'])
def index():
    task_form = TaskForm()
    mark_form = MarkDoneForm()
    delete_form = DeleteForm()
    edit_form = EditForm()

    tasks_list = get_tasks()  # 🔽 теперь через сервис

    if task_form.validate_on_submit():
        title = task_form.title.data.strip()
        existing = Task.query.filter_by(title=title).first()
        if existing:
            flash(f'Задача "{title}" уже существует', 'warning')
        else:
            new_task = Task(title=title)
            db.session.add(new_task)
            db.session.commit()
            flash('Задача добавлена', 'success')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return '', 204
            return redirect(url_for('tasks.index'))

    return render_template('index.html',
                           tasks=tasks_list,
                           task_form=task_form,
                           mark_form=mark_form,
                           delete_form=delete_form,
                           edit_form=edit_form)


@tasks_bp.route('/mark_done', methods=['POST'])
@ajax_required(MarkDoneForm)
def mark_done(form):
    task = get_task_by_id(form.task_id.data)
    if task:
        task.done = True
        db.session.commit()
        flash(f'Задача "{task.title}" отмечена выполненной', 'info')


@tasks_bp.route('/delete', methods=['POST'])
@ajax_required(DeleteForm)
def delete_task(form):
    task = get_task_by_id(form.task_id.data)
    if task:
        db.session.delete(task)
        db.session.commit()
        flash(f'Задача "{task.title}" удалена', 'info')


@tasks_bp.route('/edit', methods=['POST'])
@ajax_required(EditForm)
def edit_task(form):
    task = get_task_by_id(form.task_id.data)
    if task:
        new_title = form.title.data.strip()
        duplicate = Task.query.filter_by(title=new_title).first()
        if duplicate and duplicate.id != task.id:
            flash(f'Название "{new_title}" уже используется другой задачей', 'warning')
        else:
            task.title = new_title
            task.done = bool(form.done.data)
            db.session.commit()
            flash(f'Задача "{task.title}" обновлена', 'success')


@tasks_bp.route('/tasks_data', methods=['GET'])
def tasks_data():
    filter_val = request.args.get('filter', 'all')
    search_term = request.args.get('q', '').strip()
    sort_order = request.args.get('sort', 'asc')

    filtered_tasks = get_tasks(filter_val, search_term, sort_order)
    mark_form = MarkDoneForm()
    delete_form = DeleteForm()
    edit_form = EditForm()

    return render_template('tasks_list_partial.html',
                           tasks=filtered_tasks,
                           mark_form=mark_form,
                           delete_form=delete_form,
                           edit_form=edit_form)
