"""add board follow notifications

Revision ID: 5b7cfea17891
Revises: 9a1f2c7d4e60
Create Date: 2026-11-18 17:19:58.786301

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5b7cfea17891'
down_revision = '9a1f2c7d4e60'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "board_follow_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("follower_user_id", sa.Integer(), nullable=False),
        sa.Column("board_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["board_id"], ["boards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["follower_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_board_follow_notifications_board_id",
        "board_follow_notifications",
        ["board_id"],
    )
    op.create_index(
        "ix_board_follow_notifications_follower_user_id",
        "board_follow_notifications",
        ["follower_user_id"],
    )
    op.create_index(
        "ix_board_follow_notifications_owner_user_id",
        "board_follow_notifications",
        ["owner_user_id"],
    )


def downgrade():
    op.drop_index("ix_board_follow_notifications_owner_user_id", table_name="board_follow_notifications")
    op.drop_index("ix_board_follow_notifications_follower_user_id", table_name="board_follow_notifications")
    op.drop_index("ix_board_follow_notifications_board_id", table_name="board_follow_notifications")
    op.drop_table("board_follow_notifications")
