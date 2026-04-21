import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

assert config.config_file_name is not None
fileConfig(config.config_file_name)

# Import all capra models so Alembic can auto-detect schema changes
from app.models import SQLModel  # noqa: F401, E402
from app.models.rbi_macro_data import RBIMacroData  # noqa: F401, E402
from app.models.revoked_token import RevokedToken  # noqa: F401, E402
from app.models.score_snapshot import ScoreSnapshot  # noqa: F401, E402
from app.models.screener_data import ScreenerData  # noqa: F401, E402
from app.models.user import User  # noqa: F401, E402
from app.core.config import settings  # noqa: E402

target_metadata = SQLModel.metadata


def get_url() -> str:
    return str(settings.SQLALCHEMY_DATABASE_URI)


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    assert configuration is not None
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
