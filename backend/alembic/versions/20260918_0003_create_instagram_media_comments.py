"""create instagram media and comments

Revision ID: 20260918_0003
Revises: 20260918_0002
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260918_0003"
down_revision: str | None = "20260918_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "instagram_media",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instagram_account_id", sa.Integer(), nullable=False),
        sa.Column("instagram_media_id", sa.String(length=64), nullable=False),
        sa.Column("media_type", sa.String(length=32), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("media_url", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        sa.Column("permalink", sa.Text(), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["instagram_account_id"], ["instagram_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "instagram_account_id",
            "instagram_media_id",
            name="uq_instagram_media_account",
        ),
    )
    op.create_index(
        op.f("ix_instagram_media_instagram_account_id"),
        "instagram_media",
        ["instagram_account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instagram_media_instagram_media_id"),
        "instagram_media",
        ["instagram_media_id"],
        unique=False,
    )

    op.create_table(
        "instagram_comments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instagram_media_id", sa.Integer(), nullable=False),
        sa.Column("instagram_comment_id", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("commented_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["instagram_media_id"], ["instagram_media.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "instagram_media_id",
            "instagram_comment_id",
            name="uq_instagram_comment_media",
        ),
    )
    op.create_index(
        op.f("ix_instagram_comments_instagram_media_id"),
        "instagram_comments",
        ["instagram_media_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instagram_comments_instagram_comment_id"),
        "instagram_comments",
        ["instagram_comment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_instagram_comments_instagram_comment_id"), table_name="instagram_comments")
    op.drop_index(op.f("ix_instagram_comments_instagram_media_id"), table_name="instagram_comments")
    op.drop_table("instagram_comments")
    op.drop_index(op.f("ix_instagram_media_instagram_media_id"), table_name="instagram_media")
    op.drop_index(op.f("ix_instagram_media_instagram_account_id"), table_name="instagram_media")
    op.drop_table("instagram_media")
