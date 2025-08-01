from .models import Task

def get_tasks(filter_val='all', search_term='', sort_order='asc'):
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
    return query.all()