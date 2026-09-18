"""instagram connection health

Revision ID: 20260918_0010
Revises: 20260918_0009
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260918_0010"
down_revision: str | None = "20260918_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "instagram_accounts",
        sa.Column(
            "connection_status",
            sa.String(length=32),
            nullable=False,
            server_default="connected",
        ),
    )
    op.add_column(
        "instagram_accounts",
        sa.Column("last_connection_check_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "instagram_accounts",
        sa.Column("last_token_refreshed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "instagram_accounts",
        sa.Column("last_api_error_code", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "instagram_accounts",
        sa.Column("last_api_error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("instagram_accounts", "last_api_error_message")
    op.drop_column("instagram_accounts", "last_api_error_code")
    op.drop_column("instagram_accounts", "last_token_refreshed_at")
    op.drop_column("instagram_accounts", "last_connection_check_at")
    op.drop_column("instagram_accounts", "connection_status")
