import json

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.coding_data import CODING_EXERCISES
from app.curriculum import SUBTOPICS, TASK_TEMPLATE, TOPICS
from app.lessons_bank import all_lessons
from app.models import CodingExercise, Lesson, Project, Question, StudyTask, Subtopic, Topic
from app.projects_data import PROJECTS
from app.question_generator import COUNTS, generate_questions


def _topic_map(db: Session) -> dict[str, Topic]:
    return {topic.slug: topic for topic in db.scalars(select(Topic)).all()}


def _seed_catalog(db: Session) -> None:
    topics: dict[str, Topic] = {}
    for spec in TOPICS:
        topic = Topic(**spec)
        db.add(topic)
        db.flush()
        topics[topic.slug] = topic
        for sequence, task in enumerate(TASK_TEMPLATE, 1):
            db.add(StudyTask(topic_id=topic.id, sequence=sequence, **task))

    subtopics: dict[str, Subtopic] = {}
    for topic_slug, specs in SUBTOPICS.items():
        for spec in specs:
            row = Subtopic(topic_id=topics[topic_slug].id, **spec)
            db.add(row)
            db.flush()
            subtopics[row.slug] = row

    for spec in all_lessons():
        data = dict(spec)
        topic = topics[data.pop("topic")]
        db.add(Lesson(topic_id=topic.id, **data))

    _sync_questions(db, topics, subtopics)
    _sync_coding(db, topics)
    _sync_projects(db, topics)
    db.commit()


def _sync_questions(
    db: Session, topics: dict[str, Topic], subtopics: dict[str, Subtopic]
) -> None:
    expected = len(subtopics) * sum(COUNTS.values())
    if db.scalar(select(func.count(Question.id))) == expected:
        return
    db.execute(delete(Question))
    mappings: list[dict] = []
    topic_position = {spec["slug"]: (spec["round"], spec["sequence"]) for spec in TOPICS}
    for topic_slug, specs in SUBTOPICS.items():
        round_number, topic_sequence = topic_position[topic_slug]
        for spec in specs:
            rows = generate_questions(
                topic_slug=topic_slug,
                topic_code=f"R{round_number}T{topic_sequence:02d}",
                subtopic_slug=spec["slug"],
                subtopic_code=f"S{spec['sequence']}",
                title=spec["title"],
                summary=spec["summary"],
            )
            mappings.extend({
                "topic_id": topics[topic_slug].id,
                "subtopic_id": subtopics[spec["slug"]].id,
                "public_id": row["public_id"],
                "qtype": row["qtype"],
                "difficulty": row["difficulty"],
                "prompt": row["prompt"],
                "answer": row["answer"],
                "explanation": row["explanation"],
                "hints_json": json.dumps(row["hints"]),
                "choices_json": json.dumps(row["choices"]),
                "tags": row["tags"],
                "available": row["available"],
            } for row in rows)
    db.bulk_insert_mappings(Question, mappings)


def _sync_coding(db: Session, topics: dict[str, Topic]) -> None:
    existing = {slug for (slug,) in db.execute(select(CodingExercise.slug)).all()}
    for spec in CODING_EXERCISES:
        if spec["slug"] in existing:
            continue
        data = dict(spec)
        topic = topics[data.pop("topic")]
        db.add(CodingExercise(topic_id=topic.id, hints_json=json.dumps(data.pop("hints")), **data))


def _sync_projects(db: Session, topics: dict[str, Topic]) -> None:
    existing = {slug for (slug,) in db.execute(select(Project.slug)).all()}
    for spec in PROJECTS:
        if spec["slug"] in existing:
            continue
        data = dict(spec)
        topic = topics[data.pop("topic")]
        db.add(Project(topic_id=topic.id, hints_json=json.dumps(data.pop("hints")), **data))


def seed_if_empty(db: Session) -> None:
    """Seed catalog data only; users are created exclusively through auth."""
    if db.scalar(select(Topic.id).limit(1)):
        topics = _topic_map(db)
        subtopics = {row.slug: row for row in db.scalars(select(Subtopic)).all()}
        _sync_questions(db, topics, subtopics)
        _sync_coding(db, topics)
        _sync_projects(db, topics)
        db.commit()
        return
    _seed_catalog(db)
