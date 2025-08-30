from flask import Blueprint, render_template, redirect, url_for, request, g
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from todo_app.forms import TaskForm, MarkDoneForm, DeleteForm, EditForm, BulkDeleteForm
from todo_app.models import db, Task
from todo_app.services import get_tasks, count_tasks
from sqlalchemy import delete
from todo_app.utils import ajax_required, is_ajax, ok, bad_request, first_error

tasks_bp = Blueprint('tasks', __name__)


def get_task_by_id(id_str):
    try:
        task_id = int(id_str)
    except ValueError:
        return None
    cache = getattr(g, 'task_cache', None)
    if cache is None:
        cache = {}
        g.task_cache = cache
    task = cache.get(task_id)
    if task is None:
        task = db.session.get(Task, task_id)
        if task is not None:
            cache[task_id] = task
    if not task:
        return None
    # Проверка владения: админ видит всё
    if current_user.is_authenticated and (task.user_id == current_user.id or getattr(current_user, 'is_admin', False)):
        return task
    # Если задача без владельца (наследие), считаем общедоступной только на чтение списка
    if task.user_id is None:
        return task
    return None

@tasks_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Главная: список задач и добавление.
    AJAX: 200 JSON при успехе (message), 400 JSON с сообщением при ошибке.
    """
    task_form = TaskForm()
    mark_form = MarkDoneForm()
    delete_form = DeleteForm()
    edit_form = EditForm()
    bulk_form = BulkDeleteForm()

    # Сначала обработаем форму (POST может быть интенсивным) — затем перечитаем список при необходимости
    is_ajax_req = is_ajax()
    if task_form.validate_on_submit():
        title = (task_form.title.data or '').strip()
        # Предварительная проверка уникальности в рамках текущего пользователя
        exists_stmt = db.select(Task.id).where(
            Task.user_id == current_user.id,
            Task.title == title,
        ).limit(1)
        exists_id = db.session.execute(exists_stmt).scalar_one_or_none()
        if exists_id is not None:
            msg = f'Задача "{title}" уже существует'
            if is_ajax_req:
                return bad_request(msg)
            task_form.title.errors.append(msg)
            return render_template('index.html',
                                   tasks=[], page=1, per_page=15, total=0,
                                   task_form=task_form,
                                   mark_form=mark_form,
                                   delete_form=delete_form,
                                   edit_form=edit_form,
                                   bulk_form=bulk_form)
        new_task = Task(title=title, user_id=current_user.id)
        db.session.add(new_task)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            # На случай устаревших ограничений в БД или иных нарушений целостности
            msg = f'Не удалось добавить задачу "{title}"'
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

    # Начальная загрузка/перерисовка: показываем первую страницу задач
    page, per_page = 1, 15
    items, total = get_tasks(page=page, per_page=per_page)

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
@login_required
@ajax_required(MarkDoneForm)
def mark_done(form):
    """Отметить задачу как выполненную (поддерживает AJAX)."""
    task = get_task_by_id(form.task_id.data)
    if not task:
        return bad_request("Задача не найдена")

    # Проверка права на изменение
    if task.user_id not in (None, current_user.id) and not getattr(current_user, 'is_admin', False):
        return bad_request("Недостаточно прав")
    task.done = True
    db.session.commit()
    return ok(f'Задача "{task.title}" отмечена выполненной')


@tasks_bp.route('/delete', methods=['POST'])
@login_required
@ajax_required(DeleteForm)
def delete_task(form):
    """Удалить задачу (поддерживает AJAX)."""
    task = get_task_by_id(form.task_id.data)
    if not task:
        return bad_request("Задача не найдена")

    # Проверка права на удаление
    if task.user_id not in (None, current_user.id) and not getattr(current_user, 'is_admin', False):
        return bad_request("Недостаточно прав")
    title_for_msg = task.title
    db.session.delete(task)
    db.session.commit()
    return ok(f'Задача "{title_for_msg}" удалена')


@tasks_bp.route('/edit', methods=['POST'])
@login_required
@ajax_required(EditForm)
def edit_task(form):
    """Редактировать заголовок/статус задачи (поддерживает AJAX)."""
    task = get_task_by_id(form.task_id.data)
    if not task:
        return bad_request("Задача не найдена")

    # Проверка права на редактирование
    if task.user_id not in (None, current_user.id) and not getattr(current_user, 'is_admin', False):
        return bad_request("Недостаточно прав")
    new_title = (form.title.data or '').strip()
    # Предварительная проверка уникальности в рамках пользователя
    exists_stmt = db.select(Task.id).where(
        Task.user_id == (task.user_id if task.user_id is not None else current_user.id),
        Task.title == new_title,
        Task.id != task.id,
    ).limit(1)
    exists_id = db.session.execute(exists_stmt).scalar_one_or_none()
    if exists_id is not None:
        form.title.errors.append(f'Название "{new_title}" уже используется другой задачей')
        return None
    try:
        task.title = new_title
        task.done = bool(form.done.data)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        form.title.errors.append('Не удалось сохранить изменения')
    else:
        return ok(f'Задача "{task.title}" обновлена')


@tasks_bp.route('/tasks_data', methods=['GET'])
@login_required
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

    # Поддержка админ-страницы задач пользователя
    for_user_id = None
    if getattr(current_user, 'is_admin', False):
        user_id_param = request.args.get('user_id')
        if user_id_param and user_id_param.isdigit():
            for_user_id = int(user_id_param)

    # Сначала узнаём total (без выборки элементов), затем нормализуем страницу
    total = count_tasks(filter_val, search_term, for_user_id)
    # Корректируем границы страниц: минимум 1 страница даже при total=0
    total_pages = (total + per_page - 1) // per_page
    if total_pages < 1:
        total_pages = 1
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    # Теперь единственным запросом читаем элементы целевой страницы
    items = get_tasks(filter_val, search_term, sort_order, page=page, per_page=per_page, for_user_id=for_user_id, compute_total=False)
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
@login_required
@ajax_required(BulkDeleteForm)
def bulk_delete(form):
    # 1) распарсить ids
    raw = (form.ids.data or '').strip()
    try:
        ids = [int(x) for x in raw.split(',') if x.strip()]
    except ValueError:
        return bad_request("Некорректные идентификаторы")
    if not ids:
        return bad_request("Не выбрано ни одной задачи")

    # 2) удалить все за один запрос (SQLAlchemy 2.0 style)
    # Удалять можно только свои задачи (или админ)
    if not getattr(current_user, 'is_admin', False):
        db.session.execute(delete(Task).where(Task.id.in_(ids), Task.user_id == current_user.id))
    else:
        db.session.execute(delete(Task).where(Task.id.in_(ids)))
    db.session.commit()

    # 3) ответ
    return ok(f"Удалено задач: {len(ids)}")