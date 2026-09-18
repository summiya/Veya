"""create audience insights

Revision ID: 20260918_0006
Revises: 20260918_0005
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260918_0006"
down_revision: str | None = "20260918_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audience_insights",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instagram_account_id", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("what_people_loved", sa.JSON(), nullable=False),
        sa.Column("constructive_feedback", sa.JSON(), nullable=False),
        sa.Column("recurring_complaints", sa.JSON(), nullable=False),
        sa.Column("common_questions", sa.JSON(), nullable=False),
        sa.Column("content_suggestions", sa.JSON(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("source_comment_count", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["instagram_account_id"],
            ["instagram_accounts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audience_insights_instagram_account_id"),
        "audience_insights",
        ["instagram_account_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_audience_insights_instagram_account_id"),
        table_name="audience_insights",
    )
    op.drop_table("audience_insights")
