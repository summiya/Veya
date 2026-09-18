"""create audience health snapshots

Revision ID: 20260918_0007
Revises: 20260918_0006
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260918_0007"
down_revision: str | None = "20260918_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audience_health_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instagram_account_id", sa.Integer(), nullable=False),
        sa.Column("analyzed_comment_count", sa.Integer(), nullable=False),
        sa.Column("positive", sa.Integer(), nullable=False),
        sa.Column("neutral", sa.Integer(), nullable=False),
        sa.Column("negative", sa.Integer(), nullable=False),
        sa.Column("positive_percentage", sa.Float(), nullable=False),
        sa.Column("neutral_percentage", sa.Float(), nullable=False),
        sa.Column("negative_percentage", sa.Float(), nullable=False),
        sa.Column("constructive", sa.Integer(), nullable=False),
        sa.Column("toxic", sa.Integer(), nullable=False),
        sa.Column("severe_abuse", sa.Integer(), nullable=False),
        sa.Column("spam", sa.Integer(), nullable=False),
        sa.Column("shielded", sa.Integer(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["instagram_account_id"],
            ["instagram_accounts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audience_health_snapshots_instagram_account_id"),
        "audience_health_snapshots",
        ["instagram_account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audience_health_snapshots_captured_at"),
        "audience_health_snapshots",
        ["captured_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_audience_health_snapshots_captured_at"),
        table_name="audience_health_snapshots",
    )
    op.drop_index(
        op.f("ix_audience_health_snapshots_instagram_account_id"),
        table_name="audience_health_snapshots",
    )
    op.drop_table("audience_health_snapshots")
