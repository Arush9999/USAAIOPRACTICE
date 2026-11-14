from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80), default="Student")
    theme: Mapped[str] = mapped_column(String(16), default="system")
    weekly_hours: Mapped[int] = mapped_column(Integer, default=11)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    round: Mapped[int] = mapped_column(Integer, index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    phase: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(160))
    summary: Mapped[str] = mapped_column(Text)
    prerequisites: Mapped[str] = mapped_column(Text, default="")

    lessons: Mapped[list["Lesson"]] = relationship(back_populates="topic")
    subtopics: Mapped[list["Subtopic"]] = relationship(back_populates="topic")
    questions: Mapped[list["Question"]] = relationship(back_populates="topic")
    tasks: Mapped[list["StudyTask"]] = relationship(back_populates="topic")
    coding_exercises: Mapped[list["CodingExercise"]] = relationship(back_populates="topic")
    projects: Mapped[list["Project"]] = relationship(back_populates="topic")


class Subtopic(Base):
    __tablename__ = "subtopics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    sequence: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(Text)

    topic: Mapped[Topic] = relationship(back_populates="subtopics")
    questions: Mapped[list["Question"]] = relationship(back_populates="subtopic")


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    stage: Mapped[str] = mapped_column(String(32), default="learn")
    body_markdown: Mapped[str] = mapped_column(Text)
    available: Mapped[bool] = mapped_column(Boolean, default=True)

    topic: Mapped[Topic] = relationship(back_populates="lessons")
    completions: Mapped[list["LessonCompletion"]] = relationship(back_populates="lesson")


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (Index("ix_questions_subtopic_difficulty", "subtopic_id", "difficulty"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    subtopic_id: Mapped[int] = mapped_column(ForeignKey("subtopics.id"), nullable=False)
    qtype: Mapped[str] = mapped_column(String(32))
    difficulty: Mapped[str] = mapped_column(String(24))
    prompt: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    hints_json: Mapped[str] = mapped_column(Text)
    choices_json: Mapped[str] = mapped_column(Text, default="[]")
    tags: Mapped[str] = mapped_column(String(240), default="")
    available: Mapped[bool] = mapped_column(Boolean, default=True)

    topic: Mapped[Topic] = relationship(back_populates="questions")
    subtopic: Mapped[Subtopic] = relationship(back_populates="questions")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="question")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)
    submitted: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    question: Mapped[Question] = relationship(back_populates="attempts")


class Mastery(Base):
    __tablename__ = "mastery"
    __table_args__ = (UniqueConstraint("user_id", "topic_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    theory_score: Mapped[float] = mapped_column(Float, default=0.0)
    coding_score: Mapped[float] = mapped_column(Float, default=0.0)
    theory_attempts: Mapped[int] = mapped_column(Integer, default=0)
    coding_attempts: Mapped[int] = mapped_column(Integer, default=0)


class StudyTask(Base):
    __tablename__ = "study_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(32))
    detail: Mapped[str] = mapped_column(Text, default="")

    topic: Mapped[Topic] = relationship(back_populates="tasks")
    completions: Mapped[list["TaskCompletion"]] = relationship(back_populates="task")


class TaskCompletion(Base):
    __tablename__ = "task_completions"
    __table_args__ = (UniqueConstraint("user_id", "task_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("study_tasks.id"), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task: Mapped[StudyTask] = relationship(back_populates="completions")


class LessonCompletion(Base):
    __tablename__ = "lesson_completions"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lesson: Mapped[Lesson] = relationship(back_populates="completions")


class DailyActivity(Base):
    __tablename__ = "daily_activity"
    __table_args__ = (UniqueConstraint("user_id", "day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    day: Mapped[str] = mapped_column(String(10), index=True)
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    actions: Mapped[int] = mapped_column(Integer, default=0)


class CodingExercise(Base):
    __tablename__ = "coding_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    prompt: Mapped[str] = mapped_column(Text)
    starter_code: Mapped[str] = mapped_column(Text)
    tests_code: Mapped[str] = mapped_column(Text)
    solution_code: Mapped[str] = mapped_column(Text, default="")
    hints_json: Mapped[str] = mapped_column(Text, default="[]")

    topic: Mapped[Topic] = relationship(back_populates="coding_exercises")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    round: Mapped[int] = mapped_column(Integer, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    objectives: Mapped[str] = mapped_column(Text)
    requirements: Mapped[str] = mapped_column(Text)
    math_notes: Mapped[str] = mapped_column(Text)
    starter_code: Mapped[str] = mapped_column(Text)
    tests_code: Mapped[str] = mapped_column(Text)
    rubric: Mapped[str] = mapped_column(Text)
    hints_json: Mapped[str] = mapped_column(Text, default="[]")

    topic: Mapped[Topic] = relationship(back_populates="projects")


class ProjectProgress(Base):
    __tablename__ = "project_progress"
    __table_args__ = (UniqueConstraint("user_id", "project_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    last_code: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PracticeTest(Base):
    __tablename__ = "practice_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mode: Mapped[str] = mapped_column(String(32))
    round_filter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(24), default="mixed")
    question_ids_json: Mapped[str] = mapped_column(Text)
    answers_json: Mapped[str] = mapped_column(Text, default="{}")
    time_limit_sec: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
