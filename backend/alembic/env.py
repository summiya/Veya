from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from veya.core.config import settings
from veya.domain.authentication.models import RefreshToken  # noqa: F401
from veya.domain.insights.models import AudienceInsight  # noqa: F401
from veya.domain.instagram.models import (  # noqa: F401
    InstagramAccount,
    InstagramComment,
    InstagramMedia,
)
from veya.domain.safety.models import CommentSafety  # noqa: F401
from veya.domain.sentiment.models import CommentSentiment  # noqa: F401
from veya.domain.users.models import User  # noqa: F401
from veya.infrastructure.database.session import Base


config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
