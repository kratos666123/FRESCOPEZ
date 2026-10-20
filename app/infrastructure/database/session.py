from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.infrastructure.config.settings import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args=settings.db_connect_args,   # <-- NUEVO
    pool_pre_ping=True,
    pool_recycle=280,                        # <-- antes 3600
    pool_size=5,                             # <-- antes 10
    max_overflow=5,                          # <-- antes 20
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    """FastAPI dependency for DB session injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
