from sqlalchemy import select, func
from .models import db, Task

def get_tasks(
    filter_val: str = 'all',
    search_term: str = '',
    sort_order: str = 'asc',
    page: int | None = None,
    per_page: int | None = None,
):
    """Получить задачи с учётом фильтра, поиска и сортировки (SQLAlchemy 2.0 style).

    - filter_val: 'all' | 'done' | 'undone'
    - search_term: подстрока для поиска по названию (ILIKE)
    - sort_order: 'asc' | 'desc' по полю date_created
    - page, per_page: пагинация. Если заданы, возвращает кортеж (items, total)
    """
    stmt = select(Task)

    if filter_val == 'done':
        stmt = stmt.where(Task.done.is_(True))
    elif filter_val == 'undone':
        stmt = stmt.where(Task.done.is_(False))

    if search_term:
        stmt = stmt.where(Task.title.ilike(f'%{search_term}%'))

    if sort_order == 'asc':
        stmt = stmt.order_by(Task.date_created.asc())
    else:
        stmt = stmt.order_by(Task.date_created.desc())

    # Пагинация
    if page and per_page:
        # Подсчёт общего количества (без order_by)
        count_stmt = select(func.count()).select_from(Task)
        # Применяем те же where-фильтры
        if filter_val == 'done':
            count_stmt = count_stmt.where(Task.done.is_(True))
        elif filter_val == 'undone':
            count_stmt = count_stmt.where(Task.done.is_(False))
        if search_term:
            count_stmt = count_stmt.where(Task.title.ilike(f'%{search_term}%'))

        total = db.session.execute(count_stmt).scalar_one()

        offset_val = max(0, (page - 1) * per_page)
        stmt_paged = stmt.offset(offset_val).limit(per_page)
        items = db.session.execute(stmt_paged).scalars().all()
        return items, total

    result = db.session.execute(stmt)
    return result.scalars().all()