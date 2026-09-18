"""create instagram accounts

Revision ID: 20260918_0002
Revises: 20260918_0001
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260918_0002"
down_revision: str | None = "20260918_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "instagram_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("instagram_user_id", sa.String(length=64), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("access_token_encrypted", sa.String(length=2048), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "instagram_user_id",
            name="uq_instagram_account_user",
        ),
    )
    op.create_index(
        op.f("ix_instagram_accounts_user_id"),
        "instagram_accounts",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_instagram_accounts_instagram_user_id"),
        "instagram_accounts",
        ["instagram_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_instagram_accounts_instagram_user_id"),
        table_name="instagram_accounts",
    )
    op.drop_index(
        op.f("ix_instagram_accounts_user_id"),
        table_name="instagram_accounts",
    )
    op.drop_table("instagram_accounts")
