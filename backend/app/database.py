from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATA_DIR, settings


class Base(DeclarativeBase):
    pass


def _sqlite_connect_args(url: str) -> dict:
    return {"check_same_thread": False} if url.startswith("sqlite") else {}


engine = create_engine(
    settings.database_url,
    connect_args=_sqlite_connect_args(settings.database_url),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_engine(database_url: str | None = None):
    """Used by tests to point at an isolated database."""
    global engine, SessionLocal
    url = database_url or settings.database_url
    if url.startswith("sqlite") and not url.endswith(":memory:"):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args=_sqlite_connect_args(url))
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return engine
