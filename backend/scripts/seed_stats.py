"""Print the size of the configured generated practice bank."""

from sqlalchemy import func, select

from app.database import SessionLocal
from app.main import app  # noqa: F401 - initializes and seeds the configured database
from app.models import Question, Subtopic


with SessionLocal() as db:
    print(f"Total questions: {db.scalar(select(func.count(Question.id)))}")
    print(f"Subtopic count: {db.scalar(select(func.count(Subtopic.id)))}")
