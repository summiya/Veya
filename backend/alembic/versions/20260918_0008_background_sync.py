"""background sync

Revision ID: 20260918_0008
Revises: 20260918_0007
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260918_0008"
down_revision: str | None = "20260918_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "instagram_accounts",
        sa.Column("sync_status", sa.String(length=32), nullable=False, server_default="idle"),
    )
    op.add_column(
        "instagram_accounts",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "instagram_accounts",
        sa.Column("next_sync_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "instagram_accounts",
        sa.Column("last_sync_error", sa.Text(), nullable=True),
    )
    op.create_index(
        op.f("ix_instagram_accounts_next_sync_at"),
        "instagram_accounts",
        ["next_sync_at"],
        unique=False,
    )

    op.create_table(
        "instagram_sync_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instagram_account_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("trigger", sa.String(length=32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("media_synced", sa.Integer(), nullable=False),
        sa.Column("comments_synced", sa.Integer(), nullable=False),
        sa.Column("sentiment_analyzed", sa.Integer(), nullable=False),
        sa.Column("safety_analyzed", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["instagram_account_id"],
            ["instagram_accounts.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_instagram_sync_jobs_instagram_account_id"),
        "instagram_sync_jobs",
        ["instagram_account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instagram_sync_jobs_status"),
        "instagram_sync_jobs",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_instagram_sync_jobs_status"), table_name="instagram_sync_jobs")
    op.drop_index(
        op.f("ix_instagram_sync_jobs_instagram_account_id"),
        table_name="instagram_sync_jobs",
    )
    op.drop_table("instagram_sync_jobs")

    op.drop_index(
        op.f("ix_instagram_accounts_next_sync_at"),
        table_name="instagram_accounts",
    )
    op.drop_column("instagram_accounts", "last_sync_error")
    op.drop_column("instagram_accounts", "next_sync_at")
    op.drop_column("instagram_accounts", "last_synced_at")
    op.drop_column("instagram_accounts", "sync_status")
