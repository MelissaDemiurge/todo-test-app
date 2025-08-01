from flask import Blueprint, render_template, redirect, url_for, flash, request
from .forms import TaskForm, MarkDoneForm, DeleteForm, EditForm
from .models import db, Task

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

    tasks_list = Task.query.order_by(Task.date_created).all()

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
    # Если форма не валидна или название дублирует существующее, попадем сюда (отобразим страницу заново)

    return render_template('index.html',
                           tasks=tasks_list,
                           task_form=task_form,
                           mark_form=mark_form,
                           delete_form=delete_form,
                           edit_form=edit_form)

@tasks_bp.route('/mark_done', methods=['POST'])
def mark_done():
    form = MarkDoneForm()
    if form.validate_on_submit():
        task = get_task_by_id(form.task_id.data)
        if task:
            task.done = True
            db.session.commit()
            flash(f'Задача "{task.title}" отмечена выполненной', 'info')
    else:
        flash('Не удалось подтвердить действие', 'danger')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return '', 204
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/delete', methods=['POST'])
def delete_task():
    form = DeleteForm()
    if form.validate_on_submit():
        task = get_task_by_id(form.task_id.data)
        if task:
            db.session.delete(task)
            db.session.commit()
            flash(f'Задача "{task.title}" удалена', 'info')
    else:
        flash('Не удалось подтвердить действие', 'danger')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return '', 204
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/edit', methods=['POST'])
def edit_task():
    form = EditForm()
    if form.validate_on_submit():
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
    else:
        flash('Не удалось подтвердить действие', 'danger')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return '', 204
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/tasks_data', methods=['GET'])
def tasks_data():
    filter_val = request.args.get('filter', 'all')
    search_term = request.args.get('q', '').strip()
    sort_order = request.args.get('sort', 'asc')

    query = Task.query

    if filter_val == 'done':
        query = query.filter_by(done=True)
    elif filter_val == 'undone':
        query = query.filter_by(done=False)

    if search_term:
        query = query.filter(Task.title.ilike(f'%{search_term}%'))

    if sort_order == 'asc':
        query = query.order_by(Task.date_created.asc())
    else:
        query = query.order_by(Task.date_created.desc())

    filtered_tasks = query.all()
    mark_form = MarkDoneForm()
    delete_form = DeleteForm()
    edit_form = EditForm()

    return render_template('tasks_list_partial.html', tasks=filtered_tasks, mark_form=mark_form, delete_form=delete_form, edit_form=edit_form)
