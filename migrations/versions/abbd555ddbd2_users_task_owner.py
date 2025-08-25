from alembic import op
import sqlalchemy as sa

revision = 'abbd555ddbd2'
down_revision = '6147a1baa06c'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1) users (создать, если нет)
    if 'users' not in insp.get_table_names():
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('username', sa.String(24), nullable=False),
            sa.Column('email', sa.String(254), nullable=True),
            sa.Column('password_hash', sa.String(256), nullable=False),
            sa.Column('role', sa.String(16), nullable=False, server_default='user'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.UniqueConstraint('username'),
            sa.UniqueConstraint('email'),
        )
        op.create_index('ix_users_username', 'users', ['username'])
        op.create_index('ix_users_email', 'users', ['email'])
        op.create_index('ix_users_role', 'users', ['role'])

    # 2) tasks.user_id + FK + уникальность (без ломания существующих индексов)
    cols = {c['name'] for c in insp.get_columns('tasks')}
    uqs = {uc.get('name') for uc in insp.get_unique_constraints('tasks')}

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        if 'user_id' not in cols:
            batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
            batch_op.create_index('ix_tasks_user_id', ['user_id'], unique=False)
            batch_op.create_foreign_key(
                'fk_tasks_user_id_users', 'users',
                ['user_id'], ['id'], ondelete='CASCADE'
            )
        if 'uq_tasks_user_title' not in uqs:
            try:
                batch_op.create_unique_constraint('uq_tasks_user_title', ['user_id', 'title'])
            except Exception:
                pass

def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    uqs = {uc.get('name') for uc in insp.get_unique_constraints('tasks')}
    cols = {c['name'] for c in insp.get_columns('tasks')}

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        if 'uq_tasks_user_title' in uqs:
            batch_op.drop_constraint('uq_tasks_user_title', type_='unique')
        try:
            batch_op.drop_constraint('fk_tasks_user_id_users', type_='foreignkey')
        except Exception:
            pass
        if 'user_id' in cols:
            try:
                batch_op.drop_index('ix_tasks_user_id')
            except Exception:
                pass
            batch_op.drop_column('user_id')

    if 'users' in insp.get_table_names():
        op.drop_table('users')