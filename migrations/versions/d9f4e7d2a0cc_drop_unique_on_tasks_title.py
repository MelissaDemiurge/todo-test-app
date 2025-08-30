"""drop unique on tasks.title (keep (user_id, title))

Revision ID: d9f4e7d2a0cc
Revises: 597a077e1bbe
Create Date: 2025-08-29 00:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9f4e7d2a0cc'
down_revision = '597a077e1bbe'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Соберём имена UQ и уникальных индексов только по колонке title
    uq_names_to_drop: list[str] = []
    for uc in insp.get_unique_constraints('tasks'):
        cols = set((uc.get('column_names') or []))
        if cols == {'title'}:
            if uc.get('name'):
                uq_names_to_drop.append(uc['name'])

    idx_names_to_drop: list[str] = []
    for ix in insp.get_indexes('tasks'):
        cols = set((ix.get('column_names') or []))
        if ix.get('unique') and cols == {'title'} and ix.get('name'):
            idx_names_to_drop.append(ix['name'])

    # SQLite: batch_alter_table выполнит пересоздание таблицы при необходимости
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        for uq_name in uq_names_to_drop:
            batch_op.drop_constraint(uq_name, type_='unique')
        for idx_name in idx_names_to_drop:
            batch_op.drop_index(idx_name)


def downgrade():
    # Восстановим уникальность на title (логически не требуется, но для симметрии)
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        try:
            batch_op.create_unique_constraint('uq_tasks_title', ['title'])
        except Exception:
            # Если уже существует — пропустим
            pass


