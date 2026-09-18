"""create comment sentiments

Revision ID: 20260918_0004
Revises: 20260918_0003
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260918_0004"
down_revision: str | None = "20260918_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "comment_sentiments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instagram_comment_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("positive_score", sa.Float(), nullable=False),
        sa.Column("neutral_score", sa.Float(), nullable=False),
        sa.Column("negative_score", sa.Float(), nullable=False),
        sa.Column("compound_score", sa.Float(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["instagram_comment_id"],
            ["instagram_comments.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_comment_sentiments_instagram_comment_id"),
        "comment_sentiments",
        ["instagram_comment_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_comment_sentiments_label"),
        "comment_sentiments",
        ["label"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_comment_sentiments_label"),
        table_name="comment_sentiments",
    )
    op.drop_index(
        op.f("ix_comment_sentiments_instagram_comment_id"),
        table_name="comment_sentiments",
    )
    op.drop_table("comment_sentiments")
