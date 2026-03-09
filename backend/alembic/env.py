"""
Alembic environment configuration.

Reads DATABASE_URL from app.config.settings (pydantic-settings)
and uses SQLModel.metadata for autogenerate support.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ── Alembic Config object ────────────────────────────────────
config = context.config

# Set up Python logging from the .ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Import app settings & models ─────────────────────────────
# Import settings to get the database URL dynamically
from app.config import settings  # noqa: E402

# Import all models so SQLModel.metadata is populated
from app.models import *  # noqa: E402, F401, F403

from sqlmodel import SQLModel  # noqa: E402

# ── Target metadata for autogenerate ─────────────────────────
target_metadata = SQLModel.metadata

# ── Build the sync database URL ──────────────────────────────
# Alembic runs synchronously, so we replace asyncpg → psycopg2
_db_url = settings.database_url.replace(
    "postgresql+asyncpg://", "postgresql://"
).strip()
config.set_main_option("sqlalchemy.url", _db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL so we can emit SQL
    without needing a live database connection.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates a synchronous engine and runs migrations within
    a transaction.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,       # Detect column type changes
            compare_server_default=True,  # Detect default value changes
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
