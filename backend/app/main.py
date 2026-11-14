from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from app.config import DATA_DIR, DEFAULT_DB, SCHEMA_VERSION, settings
from app.database import Base
from app.routers import router
from app.seed import seed_if_empty

# Side-effect import so metadata includes all tables.
from app import models  # noqa: F401


def create_app() -> FastAPI:
    from app import database

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    version_file = DATA_DIR / "SCHEMA_VERSION"
    inspector = inspect(database.engine)
    tables = set(inspector.get_table_names())
    version_matches = version_file.exists() and version_file.read_text(encoding="utf-8").strip() == str(SCHEMA_VERSION)
    old_schema = "student" in tables or "students" in tables
    question_columns = {column["name"] for column in inspector.get_columns("questions")} if "questions" in tables else set()
    schema_is_current = "subtopics" in tables and "subtopic_id" in question_columns
    mismatch = bool(tables) and (old_schema or not version_matches or not schema_is_current)
    if mismatch:
        database.engine.dispose()
        database_path = Path(database.engine.url.database or "")
        if database_path.resolve() == DEFAULT_DB.resolve() and database_path.exists():
            database_path.unlink()
            database.init_engine(settings.database_url)
        else:
            Base.metadata.drop_all(bind=database.engine)
    Base.metadata.create_all(bind=database.engine)
    version_file.write_text(str(SCHEMA_VERSION), encoding="utf-8")
    with database.SessionLocal() as db:
        seed_if_empty(db)

    app = FastAPI(title=settings.app_name, version="0.1.0")
    origins = [item.strip() for item in settings.cors_origins.split(",") if item.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
