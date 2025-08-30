from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from flask_login import current_user
from .models import db, Task

def get_tasks(
    filter_val: str = 'all',
    search_term: str = '',
    sort_order: str = 'asc',
    page: int | None = None,
    per_page: int | None = None,
    for_user_id: int | None = None,
    *,
    eagerload_user: bool = False,
    compute_total: bool = True,
):
    """Получить задачи с учётом фильтра, поиска и сортировки (SQLAlchemy 2.0 style).

    - filter_val: 'all' | 'done' | 'undone'
    - search_term: подстрока для поиска по названию (ILIKE)
    - sort_order: 'asc' | 'desc' по полю date_created
    - page, per_page: пагинация. Если заданы, возвращает кортеж (items, total)
    - eagerload_user: при True загрузить владельца задач через selectinload, чтобы избежать N+1
    - compute_total: при пагинации считать total (False — быстрее, если total уже известен)
    """
    conditions = []
    # Ограничение по владельцу
    if not getattr(current_user, 'is_authenticated', False):
        # На защищённых роутов не попадём; оставим условие невозможным
        conditions.append(Task.user_id == -1)
    else:
        if getattr(current_user, 'is_admin', False):
            if for_user_id is not None:
                conditions.append(Task.user_id == for_user_id)
            # иначе админ видит свои задачи по умолчанию там, где это ожидается
            else:
                conditions.append(Task.user_id == current_user.id)
        else:
            conditions.append(Task.user_id == current_user.id)
    if filter_val == 'done':
        conditions.append(Task.done.is_(True))
    elif filter_val == 'undone':
        conditions.append(Task.done.is_(False))
    if search_term:
        conditions.append(Task.title.ilike(f'%{search_term}%'))

    stmt = select(Task).where(*conditions)
    if eagerload_user:
        stmt = stmt.options(selectinload(Task.user))

    if sort_order == 'asc':
        stmt = stmt.order_by(Task.date_created.asc(), Task.id.asc())
    else:
        stmt = stmt.order_by(Task.date_created.desc(), Task.id.desc())

    # Пагинация
    if page is not None and per_page is not None:
        total = None
        if compute_total:
            # Подсчёт общего количества (без order_by)
            count_stmt = select(func.count(1)).select_from(Task).where(*conditions)
            total = db.session.execute(count_stmt).scalar_one()

        offset_val = max(0, (page - 1) * per_page)
        stmt_paged = stmt.offset(offset_val).limit(per_page)
        items = db.session.execute(stmt_paged).scalars().all()
        if compute_total:
            return items, total
        return items

    result = db.session.execute(stmt)
    return result.scalars().all()


def count_tasks(
    filter_val: str = 'all',
    search_term: str = '',
    for_user_id: int | None = None,
):
    """Подсчитать количество задач под текущими условиями.

    Учитывает владельца, фильтр по статусу и поиск.
    """
    conditions = []
    if not getattr(current_user, 'is_authenticated', False):
        conditions.append(Task.user_id == -1)
    else:
        if getattr(current_user, 'is_admin', False):
            if for_user_id is not None:
                conditions.append(Task.user_id == for_user_id)
            else:
                conditions.append(Task.user_id == current_user.id)
        else:
            conditions.append(Task.user_id == current_user.id)

    if filter_val == 'done':
        conditions.append(Task.done.is_(True))
    elif filter_val == 'undone':
        conditions.append(Task.done.is_(False))
    if search_term:
        conditions.append(Task.title.ilike(f'%{search_term}%'))

    count_stmt = select(func.count(1)).select_from(Task).where(*conditions)
    return db.session.execute(count_stmt).scalar_one()