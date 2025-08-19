from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from sqlalchemy.exc import IntegrityError
from todo_app.forms import TaskForm, MarkDoneForm, DeleteForm, EditForm, BulkDeleteForm
from todo_app.models import db, Task
from todo_app.services import get_tasks
from todo_app.utils import ajax_required
from sqlalchemy import delete
from todo_app.utils import is_ajax, ok, bad_request, first_error

tasks_bp = Blueprint('tasks', __name__)


def get_task_by_id(id_str):
    try:
        task_id = int(id_str)
    except ValueError:
        return None
    return db.session.get(Task, task_id)

@tasks_bp.route('/', methods=['GET', 'POST'])
def index():
    """Главная: список задач и добавление.
    AJAX: 200 JSON при успехе (message), 400 JSON с сообщением при ошибке.
    """
    task_form = TaskForm()
    mark_form = MarkDoneForm()
    delete_form = DeleteForm()
    edit_form = EditForm()
    bulk_form = BulkDeleteForm()

    # Начальная загрузка страницы: покажем первую страницу задач
    page, per_page = 1, 15
    items, total = get_tasks(page=page, per_page=per_page)

    is_ajax_req = is_ajax()

    if task_form.validate_on_submit():
        title = task_form.title.data
        new_task = Task(title=title)
        db.session.add(new_task)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            msg = f'Задача "{title}" уже существует'
            if is_ajax_req:
                return bad_request(msg)
            task_form.title.errors.append(msg)
        else:
            if is_ajax_req:
                return ok("Задача добавлена")
            return redirect(url_for('tasks.index'))
    else:
        if request.method == 'POST' and is_ajax_req:
            return bad_request(first_error(task_form))

    return render_template('index.html',
                           tasks=items,
                           page=page,
                           per_page=per_page,
                           total=total,
                           task_form=task_form,
                           mark_form=mark_form,
                           delete_form=delete_form,
                           edit_form=edit_form,
                           bulk_form=bulk_form)


@tasks_bp.route('/mark_done', methods=['POST'])
@ajax_required(MarkDoneForm)
def mark_done(form):
    """Отметить задачу как выполненную (поддерживает AJAX)."""
    task = get_task_by_id(form.task_id.data)
    if not task:
        return bad_request("Задача не найдена")

    task.done = True
    db.session.commit()
    return ok(f'Задача "{task.title}" отмечена выполненной')


@tasks_bp.route('/delete', methods=['POST'])
@ajax_required(DeleteForm)
def delete_task(form):
    """Удалить задачу (поддерживает AJAX)."""
    task = get_task_by_id(form.task_id.data)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if not task:
        return bad_request("Задача не найдена")

    title_for_msg = task.title
    db.session.delete(task)
    db.session.commit()
    return ok(f'Задача "{title_for_msg}" удалена')


@tasks_bp.route('/edit', methods=['POST'])
@ajax_required(EditForm)
def edit_task(form):
    """Редактировать заголовок/статус задачи (поддерживает AJAX)."""
    task = get_task_by_id(form.task_id.data)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if not task:
        return bad_request("Задача не найдена")

    new_title = form.title.data
    task.title = new_title
    task.done = bool(form.done.data)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        form.title.errors.append(f'Название "{new_title}" уже используется другой задачей')
    else:
        return ok(f'Задача "{task.title}" обновлена')


@tasks_bp.route('/tasks_data', methods=['GET'])
def tasks_data():
    filter_val = request.args.get('filter', 'all')
    search_term = request.args.get('q', '').strip()
    sort_order = request.args.get('sort', 'asc')

    try:
        page = int(request.args.get('page', '1'))
        per_page = int(request.args.get('per_page', '15'))
    except ValueError:
        page, per_page = 1, 15
    # Ограничиваем размер страницы от 1 до 100
    per_page = min(max(per_page, 1), 100)

    # Первая выборка, чтобы узнать total
    items, total = get_tasks(filter_val, search_term, sort_order, page=page, per_page=per_page)
    # Корректируем границы страниц: минимум 1 страница даже при total=0
    total_pages = (total + per_page - 1) // per_page
    if total_pages < 1:
        total_pages = 1
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
        # Перечитываем элементы для скорректированной страницы
        items, total = get_tasks(filter_val, search_term, sort_order, page=page, per_page=per_page)
    mark_form = MarkDoneForm()
    delete_form = DeleteForm()
    edit_form = EditForm()

    bulk_form = BulkDeleteForm()
    return render_template('tasks_list_partial.html',
                           tasks=items,
                           page=page,
                           per_page=per_page,
                           total=total,
                           mark_form=mark_form,
                           delete_form=delete_form,
                           edit_form=edit_form,
                           bulk_form=bulk_form)


@tasks_bp.route('/bulk_delete', methods=['POST'])
@ajax_required(BulkDeleteForm)
def bulk_delete(form):
    # 1) распарсить ids
    raw = (form.ids.data or '').strip()
    try:
        ids = [int(x) for x in raw.split(',') if x.strip()]
    except ValueError:
        return jsonify({"success": False, "message": "Некорректные идентификаторы"}), 400
    if not ids:
        return jsonify({"success": False, "message": "Не выбрано ни одной задачи"}), 400

    # 2) удалить все за один запрос (SQLAlchemy 2.0 style)
    db.session.execute(delete(Task).where(Task.id.in_(ids)))
    db.session.commit()

    # 3) ответ
    return jsonify({
        "success": True,
        "message": f"Удалено задач: {len(ids)}"
    }), 200