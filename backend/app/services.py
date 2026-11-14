import json
import re
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Attempt, DailyActivity, Lesson, LessonCompletion, Mastery, Question, StudyTask, TaskCompletion, Topic, User

THEORY_TYPES = {"multiple_choice", "short_answer", "derivation", "proof"}
CODING_TYPES = {"coding"}


def parse_list(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()] if value else []


def load_json_list(raw: str) -> list:
    try:
        value = json.loads(raw or "[]")
        return value if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


def normalize_answer(text: str) -> str:
    cleaned = text.strip().lower().replace("```python", "").replace("```latex", "").replace("```", "")
    cleaned = re.sub(r"\s+", "", cleaned.replace("$", "").replace("\\", ""))
    return cleaned


SHORT_ALIASES = {
    "r1-py-003": {"[x*xforxinxs]", "[x**2forxinxs]", "return[x*xforxinxs]", "return[x**2forxinxs]"},
    "r1-md-002": {"begin{bmatrix}1\\2end{bmatrix}", "begin{bmatrix}1\\\\2end{bmatrix}", "begin{bmatrix}1\\\\2end{bmatrix}".replace("\\", "")},
}


def grade_submission(question: Question, submitted: str) -> bool:
    expected, got = normalize_answer(question.answer), normalize_answer(submitted)
    return got == expected or got in SHORT_ALIASES.get(question.public_id.lower(), set()) or expected.replace("top", "t") == got.replace("top", "t")


def record_activity(db: Session, user_id: int, minutes: int) -> None:
    day = date.today().isoformat()
    row = db.scalar(select(DailyActivity).where(DailyActivity.user_id == user_id, DailyActivity.day == day))
    if row is None:
        row = DailyActivity(user_id=user_id, day=day, minutes=0, actions=0)
        db.add(row)
    row.minutes += minutes
    row.actions += 1


def compute_streak(db: Session, user_id: int) -> int:
    rows = db.scalars(select(DailyActivity).where(DailyActivity.user_id == user_id)).all()
    active = {row.day for row in rows if row.actions}
    cursor = date.today()
    if cursor.isoformat() not in active:
        cursor -= timedelta(days=1)
    streak = 0
    while cursor.isoformat() in active:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def mastery_status(mastery: Mastery | None, coding_count: int = 0) -> str:
    if not mastery or not mastery.theory_attempts:
        return "not_started"
    theory_ok = mastery.theory_attempts >= 5 and mastery.theory_score >= .8
    coding_ok = not coding_count or (mastery.coding_attempts >= 3 and mastery.coding_score >= .8)
    if theory_ok and coding_ok:
        return "mastered" if coding_count else "mastered_theory"
    return "theory_ready" if theory_ok else ("in_progress" if mastery.theory_score >= .5 else "needs_work")


def refresh_mastery(db: Session, user: User, topic: Topic) -> Mastery:
    mastery = db.scalar(select(Mastery).where(Mastery.user_id == user.id, Mastery.topic_id == topic.id))
    if mastery is None:
        mastery = Mastery(user_id=user.id, topic_id=topic.id)
        db.add(mastery)
    questions = db.scalars(select(Question).where(Question.topic_id == topic.id)).all()
    qmap = {q.id: q for q in questions}
    attempts = db.scalars(select(Attempt).where(Attempt.user_id == user.id, Attempt.question_id.in_(list(qmap) or [0]))).all()
    theory = [a for a in attempts if qmap[a.question_id].qtype in THEORY_TYPES]
    coding = [a for a in attempts if qmap[a.question_id].qtype in CODING_TYPES]
    mastery.theory_attempts, mastery.coding_attempts = len(theory), len(coding)
    mastery.theory_score = sum(a.is_correct for a in theory) / len(theory) if theory else 0
    mastery.coding_score = sum(a.is_correct for a in coding) / len(coding) if coding else 0
    return mastery


def serialize_topic(db: Session, user: User, topic: Topic) -> dict:
    mastery = db.scalar(select(Mastery).where(Mastery.user_id == user.id, Mastery.topic_id == topic.id))
    lesson_ids = [lesson.id for lesson in topic.lessons]
    task_ids = [task.id for task in topic.tasks]
    lesson_done = len(db.scalars(select(LessonCompletion).where(LessonCompletion.user_id == user.id, LessonCompletion.lesson_id.in_(lesson_ids or [0]))).all())
    task_done = len(db.scalars(select(TaskCompletion).where(TaskCompletion.user_id == user.id, TaskCompletion.task_id.in_(task_ids or [0]))).all())
    coding_count = sum(q.qtype in CODING_TYPES for q in topic.questions)
    return {
        "slug": topic.slug, "round": topic.round, "sequence": topic.sequence, "phase": topic.phase,
        "title": topic.title, "summary": topic.summary, "prerequisites": parse_list(topic.prerequisites),
        "lesson_count": len(topic.lessons), "available_lessons": sum(x.available for x in topic.lessons),
        "question_count": sum(x.available for x in topic.questions),
        "theory_score": round(mastery.theory_score, 3) if mastery else 0.0,
        "coding_score": round(mastery.coding_score, 3) if mastery else 0.0,
        "mastery_status": mastery_status(mastery, coding_count),
        "completed_lessons": lesson_done, "completed_tasks": task_done, "total_tasks": len(topic.tasks),
    }


def lesson_completed(db: Session, user_id: int, lesson_id: int) -> bool:
    return db.scalar(select(LessonCompletion.id).where(LessonCompletion.user_id == user_id, LessonCompletion.lesson_id == lesson_id)) is not None


def serialize_lesson(db: Session, user_id: int, lesson: Lesson) -> dict:
    return {"slug": lesson.slug, "title": lesson.title, "stage": lesson.stage, "available": lesson.available, "completed": lesson_completed(db, user_id, lesson.id)}


def serialize_task(db: Session, user_id: int, task: StudyTask) -> dict:
    completed = db.scalar(select(TaskCompletion.id).where(TaskCompletion.user_id == user_id, TaskCompletion.task_id == task.id)) is not None
    return {"id": task.id, "topic_slug": task.topic.slug, "topic_title": task.topic.title, "round": task.topic.round, "title": task.title, "kind": task.kind, "detail": task.detail, "completed": completed}


def topic_progress(db: Session, user: User, topics: list[Topic]) -> float:
    if not topics:
        return 0.0
    values = []
    for topic in topics:
        data = serialize_topic(db, user, topic)
        lesson_fraction = data["completed_lessons"] / (data["lesson_count"] or 1)
        values.append((lesson_fraction + data["theory_score"]) / 2)
    return round(sum(values) / len(values) * 100, 1)


def overall_mastery(db: Session, user: User, topics: list[Topic]) -> float:
    return topic_progress(db, user, topics)


def continue_lesson(db: Session, user_id: int) -> Lesson | None:
    lessons = db.scalars(select(Lesson).where(Lesson.available.is_(True)).order_by(Lesson.topic_id, Lesson.sequence)).all()
    return next((lesson for lesson in lessons if not lesson_completed(db, user_id, lesson.id)), lessons[-1] if lessons else None)
