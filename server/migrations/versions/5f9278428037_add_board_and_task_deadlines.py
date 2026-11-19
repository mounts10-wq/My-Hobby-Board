"""add board and task deadlines

Revision ID: 5f9278428037
Revises: 5c9a81742f7e
Create Date: 2026-11-18 15:41:45.960582

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f9278428037'
down_revision = '5c9a81742f7e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('boards', sa.Column('target_date', sa.Date(), nullable=True))
    op.add_column('tasks', sa.Column('due_date', sa.Date(), nullable=True))


def downgrade():
    op.drop_column('tasks', 'due_date')
    op.drop_column('boards', 'target_date')
