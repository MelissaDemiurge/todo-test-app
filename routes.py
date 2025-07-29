from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from forms import TaskForm, MarkDoneForm, DeleteForm, EditForm

tasks_bp = Blueprint('tasks', __name__)

def get_task_by_index(idx_str, tasks_list):
    try:
        idx = int(idx_str)
        if 0 <= idx < len(tasks_list):
            return idx, tasks_list[idx]
        else:
            flash('Неверный индекс задачи', 'warning')
            return None, None
    except ValueError:
        flash('Индекс задачи должен быть числом', 'danger')
        return None, None

@tasks_bp.route('/', methods=['GET', 'POST'])
def index():
    task_form = TaskForm()
    mark_form = MarkDoneForm()
    delete_form = DeleteForm()
    edit_form = EditForm()

    session.setdefault('tasks', [])
    tasks_list = session['tasks']

    if task_form.validate_on_submit():
        tasks_list.append({'title': task_form.title.data.strip(), 'done': False})
        session.modified = True
        flash('Задача добавлена', 'success')
        return redirect(url_for('tasks.index'))

    return render_template('index.html',
                           tasks=tasks_list,
                           task_form=task_form,
                           mark_form=mark_form,
                           delete_form=delete_form,
                           edit_form=edit_form)

@tasks_bp.route('/mark_done', methods=['POST'])
def mark_done():
    form = MarkDoneForm()
    session.setdefault('tasks', [])
    tasks_list = session['tasks']

    if form.validate_on_submit():
        idx, task = get_task_by_index(form.task_index.data, tasks_list)
        if task is not None:
            task['done'] = True
            session.modified = True
            flash(f'Задача №{idx+1} отмечена выполненной', 'info')
    else:
        flash('Не удалось подтвердить действие', 'danger')
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/delete', methods=['POST'])
def delete_task():
    form = DeleteForm()
    session.setdefault('tasks', [])
    tasks_list = session['tasks']

    if form.validate_on_submit():
        idx, task = get_task_by_index(form.task_index.data, tasks_list)
        if task is not None:
            tasks_list.pop(idx)
            session.modified = True
            flash(f'Задача №{idx+1} удалена', 'info')
    else:
        flash('Не удалось подтвердить действие', 'danger')
    return redirect(url_for('tasks.index'))

@tasks_bp.route('/edit', methods=['POST'])
def edit_task():
    form = EditForm()
    session.setdefault('tasks', [])
    tasks_list = session['tasks']

    if form.validate_on_submit():
        idx, task = get_task_by_index(form.task_index.data, tasks_list)
        if task is not None:
            task['title'] = form.title.data.strip()
            task['done'] = True if form.done.data else False
            session.modified = True
            flash(f'Задача №{idx+1} обновлена', 'success')
    else:
        flash('Не удалось подтвердить действие', 'danger')

    return redirect(url_for('tasks.index'))
