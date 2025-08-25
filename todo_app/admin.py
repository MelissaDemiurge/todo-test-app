from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from sqlalchemy import select

from .models import db, User, Task
from .services import get_tasks
from .forms import MarkDoneForm, DeleteForm, EditForm, BulkDeleteForm


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def require_admin():
    if not (current_user.is_authenticated and getattr(current_user, 'is_admin', False)):
        abort(403)


@admin_bp.route('/users')
@login_required
def users():
    require_admin()
    users = db.session.execute(select(User).order_by(User.username.asc())).scalars().all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>')
@login_required
def user_tasks(user_id: int):
    require_admin()
    page = max(1, int(request.args.get('page', '1') or '1'))
    per_page = max(1, min(50, int(request.args.get('per_page', '15') or '15')))
    filter_val = request.args.get('filter', 'all')
    search = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'desc')

    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    items, total = get_tasks(filter_val, search, sort, page, per_page, for_user_id=user_id)
    # формы для partial-шаблона списка задач
    mark_form = MarkDoneForm()
    delete_form = DeleteForm()
    edit_form = EditForm()
    bulk_form = BulkDeleteForm()
    return render_template(
        'admin/user_tasks.html',
        target_user=user,
        tasks=items,
        page=page,
        per_page=per_page,
        total=total,
        mark_form=mark_form,
        delete_form=delete_form,
        edit_form=edit_form,
        bulk_form=bulk_form,
    )


