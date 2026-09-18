"""create comment safety

Revision ID: 20260918_0005
Revises: 20260918_0004
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260918_0005"
down_revision: str | None = "20260918_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "comment_safety",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instagram_comment_id", sa.Integer(), nullable=False),
        sa.Column("primary_label", sa.String(length=32), nullable=False),
        sa.Column("constructive_score", sa.Float(), nullable=False),
        sa.Column("toxic_score", sa.Float(), nullable=False),
        sa.Column("severe_abuse_score", sa.Float(), nullable=False),
        sa.Column("spam_score", sa.Float(), nullable=False),
        sa.Column("should_shield", sa.Boolean(), nullable=False),
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
        op.f("ix_comment_safety_instagram_comment_id"),
        "comment_safety",
        ["instagram_comment_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_comment_safety_primary_label"),
        "comment_safety",
        ["primary_label"],
        unique=False,
    )
    op.create_index(
        op.f("ix_comment_safety_should_shield"),
        "comment_safety",
        ["should_shield"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_comment_safety_should_shield"), table_name="comment_safety")
    op.drop_index(op.f("ix_comment_safety_primary_label"), table_name="comment_safety")
    op.drop_index(op.f("ix_comment_safety_instagram_comment_id"), table_name="comment_safety")
    op.drop_table("comment_safety")
