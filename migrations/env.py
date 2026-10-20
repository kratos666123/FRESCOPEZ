import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to sys.path so models can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import Base

# Import ALL models so Alembic detects them
from app.infrastructure.database.models.user_model import UserModel          # noqa: F401
from app.infrastructure.database.models.token_model import RefreshTokenModel  # noqa: F401
from app.infrastructure.database.models.category_model import CategoryModel   # noqa: F401
from app.infrastructure.database.models.product_model import ProductModel     # noqa: F401
from app.infrastructure.database.models.order_model import OrderModel, OrderItemModel  # noqa: F401
from app.infrastructure.database.models.delivery_model import DeliveryModel, DeliveryItemModel  # noqa: F401

config = context.config
settings = get_settings()

# Override sqlalchemy.url with value from .env
config.set_main_option("sqlalchemy.url", settings.database_url_alembic)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no real DB connection needed)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=settings.db_connect_args,   # <-- NUEVO
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
