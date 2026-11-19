"""add task-linked board activity

Revision ID: 9a1f2c7d4e60
Revises: 5f9278428037
Create Date: 2026-11-18

"""
from alembic import op
import sqlalchemy as sa


revision = "9a1f2c7d4e60"
down_revision = "5f9278428037"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("board_updates") as batch_op:
        batch_op.add_column(sa.Column("task_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("is_announcement", sa.Boolean(), server_default=sa.false(), nullable=False)
        )
        batch_op.create_foreign_key(
            "fk_board_updates_task_id_tasks",
            "tasks",
            ["task_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_board_updates_task_id", ["task_id"], unique=False)


def downgrade():
    with op.batch_alter_table("board_updates") as batch_op:
        batch_op.drop_index("ix_board_updates_task_id")
        batch_op.drop_constraint("fk_board_updates_task_id_tasks", type_="foreignkey")
        batch_op.drop_column("is_announcement")
        batch_op.drop_column("task_id")
