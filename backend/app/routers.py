import json
import random
import secrets
from datetime import datetime
from typing import Literal
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth import create_access_token, get_current_user, get_user_by_email, google_configured, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.models import Attempt, CodingExercise, DailyActivity, Lesson, LessonCompletion, PracticeTest, Project, ProjectProgress, Question, StudyTask, Subtopic, TaskCompletion, Topic, User
from app.schemas import AttemptIn, LoginIn, ProjectCompleteIn, SettingsIn, SignupIn, TestStartIn, TestSubmitIn, TutorChatIn
from app.services import compute_streak, continue_lesson, grade_submission, load_json_list, mastery_status, overall_mastery, parse_list, record_activity, refresh_mastery, serialize_lesson, serialize_task, serialize_topic, topic_progress

router = APIRouter(prefix="/api")


def _user(user: User) -> dict:
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "theme": user.theme, "weekly_hours": user.weekly_hours}


def _topics(db: Session) -> list[Topic]:
    return list(db.scalars(select(Topic).options(selectinload(Topic.lessons), selectinload(Topic.questions), selectinload(Topic.tasks).selectinload(StudyTask.topic)).order_by(Topic.round, Topic.sequence)).all())


def _question_out(q: Question) -> dict:
    choices = load_json_list(q.choices_json)
    random.shuffle(choices)
    return {"public_id": q.public_id, "topic_slug": q.topic.slug, "topic_title": q.topic.title, "subtopic_slug": q.subtopic.slug, "qtype": q.qtype, "difficulty": q.difficulty, "prompt": q.prompt, "choices": choices, "hints": load_json_list(q.hints_json), "tags": parse_list(q.tags), "practice_label": "Unofficial practice question"}


@router.get("/health")
def health():
    return {"ok": True}


@router.post("/auth/signup")
def signup(payload: SignupIn, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(409, "Email already registered")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password), display_name=payload.display_name.strip())
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_access_token(user.id), "token_type": "bearer", "user": _user(user)}


@router.post("/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_access_token(user.id), "token_type": "bearer", "user": _user(user)}


@router.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return _user(user)


@router.get("/auth/google/status")
def google_status():
    return {"configured": google_configured()}


@router.get("/auth/google/start")
def google_start():
    if not google_configured():
        raise HTTPException(503, "Google sign-in is not configured")
    params = {"client_id": settings.google_client_id, "redirect_uri": settings.google_redirect_uri, "response_type": "code", "scope": "openid email profile", "state": secrets.token_urlsafe(20), "access_type": "online"}
    return {"url": "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)}


@router.get("/auth/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    if not google_configured():
        raise HTTPException(503, "Google sign-in is not configured")
    token = httpx.post("https://oauth2.googleapis.com/token", data={"code": code, "client_id": settings.google_client_id, "client_secret": settings.google_client_secret, "redirect_uri": settings.google_redirect_uri, "grant_type": "authorization_code"}, timeout=15)
    if token.is_error:
        raise HTTPException(400, "Google authorization failed")
    info = httpx.get("https://openidconnect.googleapis.com/v1/userinfo", headers={"Authorization": f"Bearer {token.json()['access_token']}"}, timeout=15)
    if info.is_error:
        raise HTTPException(400, "Could not read Google profile")
    profile = info.json()
    user = db.scalar(select(User).where(User.google_sub == profile["sub"])) or get_user_by_email(db, profile["email"])
    if user is None:
        user = User(email=profile["email"].lower(), google_sub=profile["sub"], display_name=profile.get("name") or "Student")
        db.add(user)
    else:
        user.google_sub = profile["sub"]
    db.commit(); db.refresh(user)
    jwt_token = create_access_token(user.id)
    return RedirectResponse(f"{settings.frontend_url.rstrip('/')}/auth/callback?token={jwt_token}")


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topics = _topics(db); r1 = [t for t in topics if t.round == 1]; r2 = [t for t in topics if t.round == 2]
    nxt = continue_lesson(db, user.id)
    module = next((t for t in topics if serialize_topic(db, user, t)["completed_lessons"] < len(t.lessons)), topics[0] if topics else None)
    tasks = [serialize_task(db, user.id, task) for task in (module.tasks if module else [])]
    activity = db.scalars(select(DailyActivity).where(DailyActivity.user_id == user.id).order_by(DailyActivity.day.desc()).limit(35)).all()
    return {"display_name": user.display_name, "streak": compute_streak(db, user.id), "overall_mastery": overall_mastery(db, user, topics), "round1_progress": topic_progress(db, user, r1), "round2_progress": topic_progress(db, user, r2), "continue_lesson": serialize_lesson(db, user.id, nxt) if nxt else None, "continue_topic_slug": nxt.topic.slug if nxt else None, "recommended_tasks": [t for t in tasks if not t["completed"]][:3], "weakest_topics": [serialize_topic(db, user, t) for t in topics[:3]], "upcoming_module": serialize_topic(db, user, module) if module else None, "activity": [{"day": a.day, "minutes": a.minutes, "actions": a.actions} for a in activity], "weekly_hours": user.weekly_hours, "stats": {"topics": len(topics), "lessons_available": sum(len(t.lessons) for t in topics), "questions": sum(len(t.questions) for t in topics)}}


@router.get("/topics")
def list_topics(round: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topics = [t for t in _topics(db) if not round or t.round == round]
    keys = list(dict.fromkeys((t.round, t.phase) for t in topics))
    return {"tracks": [{"round": r, "phase": phase, "modules": [serialize_topic(db, user, t) for t in topics if (t.round, t.phase) == (r, phase)]} for r, phase in keys]}


@router.get("/topics/{slug}")
def topic_detail(slug: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topic = next((t for t in _topics(db) if t.slug == slug), None)
    if not topic: raise HTTPException(404, "Topic not found")
    return {"topic": serialize_topic(db, user, topic), "lessons": [serialize_lesson(db, user.id, x) for x in sorted(topic.lessons, key=lambda x: x.sequence)], "stages": ["learn", "understand", "implement", "practice", "mastery"], "tasks": [serialize_task(db, user.id, x) for x in sorted(topic.tasks, key=lambda x: x.sequence)], "question_count": len(topic.questions)}


@router.get("/lessons/{slug}")
def lesson_detail(slug: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lesson = db.scalar(select(Lesson).options(selectinload(Lesson.topic).selectinload(Topic.lessons)).where(Lesson.slug == slug))
    if not lesson: raise HTTPException(404, "Lesson not found")
    siblings = sorted(lesson.topic.lessons, key=lambda x: x.sequence); index = siblings.index(lesson)
    return {**serialize_lesson(db, user.id, lesson), "body_markdown": lesson.body_markdown, "topic_slug": lesson.topic.slug, "topic_title": lesson.topic.title, "next_slug": siblings[index+1].slug if index+1 < len(siblings) else None, "prev_slug": siblings[index-1].slug if index else None}


@router.post("/lessons/{slug}/complete")
def complete_lesson(slug: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lesson = db.scalar(select(Lesson).where(Lesson.slug == slug))
    if not lesson: raise HTTPException(404, "Lesson not found")
    if not db.scalar(select(LessonCompletion).where(LessonCompletion.user_id == user.id, LessonCompletion.lesson_id == lesson.id)):
        db.add(LessonCompletion(user_id=user.id, lesson_id=lesson.id)); record_activity(db, user.id, 1); db.commit()
    return {"ok": True, "slug": slug}


@router.get("/practice/meta")
def practice_meta(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topics = db.scalars(
        select(Topic).options(selectinload(Topic.subtopics)).order_by(Topic.round, Topic.sequence)
    ).all()
    counts = {
        (subtopic_id, difficulty): count
        for subtopic_id, difficulty, count in db.execute(
            select(Question.subtopic_id, Question.difficulty, func.count(Question.id))
            .where(Question.available.is_(True))
            .group_by(Question.subtopic_id, Question.difficulty)
        )
    }
    return {"topics": [{
        "slug": topic.slug,
        "title": topic.title,
        "round": topic.round,
        "subtopics": [{
            "slug": subtopic.slug,
            "title": subtopic.title,
            "counts": {level: counts.get((subtopic.id, level), 0) for level in ("easy", "medium", "hard")},
        } for subtopic in sorted(topic.subtopics, key=lambda item: item.sequence)],
    } for topic in topics]}


@router.get("/practice/next")
def practice_next(
    topic: str,
    difficulty: Literal["easy", "medium", "hard"],
    subtopic: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.scalar(select(Topic).where(Topic.slug == topic))
    if not row:
        raise HTTPException(404, "Topic not found")
    query = (
        select(Question)
        .options(selectinload(Question.topic), selectinload(Question.subtopic))
        .where(Question.available.is_(True), Question.topic_id == row.id, Question.difficulty == difficulty)
    )
    if subtopic:
        subtopic_row = db.scalar(
            select(Subtopic).where(Subtopic.slug == subtopic, Subtopic.topic_id == row.id)
        )
        if not subtopic_row:
            raise HTTPException(404, "Subtopic not found for this topic")
        query = query.where(Question.subtopic_id == subtopic_row.id)
    questions = list(db.scalars(query).all())
    if not questions: raise HTTPException(404, "No practice questions available")
    missed = set(db.scalars(select(Attempt.question_id).where(Attempt.user_id == user.id, Attempt.is_correct.is_(False))).all())
    return _question_out(random.choice([q for q in questions if q.id in missed] or questions))


def _submit_attempt(payload: AttemptIn, db: Session, user: User) -> dict:
    question = db.scalar(select(Question).options(selectinload(Question.topic).selectinload(Topic.questions)).where(Question.public_id == payload.public_id))
    if not question: raise HTTPException(404, "Question not found")
    correct = grade_submission(question, payload.submitted)
    db.add(Attempt(user_id=user.id, question_id=question.id, submitted=payload.submitted, is_correct=correct, hints_used=payload.hints_used))
    record_activity(db, user.id, 1); db.flush()
    mastery = refresh_mastery(db, user, question.topic); db.commit()
    return {"public_id": question.public_id, "is_correct": correct, "submitted": payload.submitted, "correct_answer": question.answer, "explanation": question.explanation, "theory_score": round(mastery.theory_score, 3), "mastery_status": mastery_status(mastery)}


@router.post("/practice/attempt")
def practice_attempt(payload: AttemptIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _submit_attempt(payload, db, user)


def _inline_checks(db: Session, topic_id: int, count: int) -> list[Question]:
    checks = list(db.scalars(
        select(Question).options(selectinload(Question.subtopic)).where(
            Question.topic_id == topic_id,
            Question.tags.like("%learn-check%"),
        ).order_by(Question.subtopic_id, Question.public_id)
    ).all())
    grouped: dict[int, list[Question]] = {}
    for question in checks:
        grouped.setdefault(question.subtopic_id, []).append(question)
    groups = list(grouped.values())
    return [
        groups[index % len(groups)][index // len(groups)]
        for index in range(min(count, sum(len(group) for group in groups)))
        if index // len(groups) < len(groups[index % len(groups)])
    ] if groups else []


def _learn_check_progress(db: Session, user_id: int, topic_id: int, lesson_count: int) -> tuple[int, int]:
    checks = [question.id for question in _inline_checks(db, topic_id, lesson_count * 2)]
    if not checks:
        return 0, 0
    correct = db.scalar(
        select(func.count(func.distinct(Attempt.question_id))).where(
            Attempt.user_id == user_id,
            Attempt.is_correct.is_(True),
            Attempt.question_id.in_(checks),
        )
    ) or 0
    return correct, len(checks)


@router.get("/learn/modules")
def learn_modules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topics = db.scalars(
        select(Topic)
        .options(selectinload(Topic.lessons))
        .order_by(Topic.round, Topic.sequence)
    ).all()
    lesson_done = set(db.scalars(
        select(LessonCompletion.lesson_id).where(LessonCompletion.user_id == user.id)
    ).all())
    modules = []
    for topic in topics:
        available_lessons = [lesson for lesson in topic.lessons if lesson.available]
        correct, total_checks = _learn_check_progress(db, user.id, topic.id, len(available_lessons))
        completed_lessons = sum(lesson.id in lesson_done for lesson in available_lessons)
        total = len(available_lessons) + total_checks
        modules.append({
            "slug": topic.slug,
            "title": topic.title,
            "summary": topic.summary,
            "round": topic.round,
            "phase": topic.phase,
            "sequence": topic.sequence,
            "progress": {
                "lessons_done": completed_lessons,
                "lessons_total": len(available_lessons),
                "checks_correct": correct,
                "checks_total": total_checks,
                "percent": round(100 * (completed_lessons + correct) / total, 1) if total else 0.0,
            },
        })
    keys = list(dict.fromkeys((item["round"], item["phase"]) for item in modules))
    return {"groups": [{
        "round": round_number,
        "phase": phase,
        "modules": [item for item in modules if (item["round"], item["phase"]) == (round_number, phase)],
    } for round_number, phase in keys]}


@router.get("/learn/modules/{topic_slug}")
def learn_module(topic_slug: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topic = db.scalar(
        select(Topic)
        .options(selectinload(Topic.lessons), selectinload(Topic.subtopics))
        .where(Topic.slug == topic_slug)
    )
    if not topic:
        raise HTTPException(404, "Topic not found")
    lessons = sorted((lesson for lesson in topic.lessons if lesson.available), key=lambda item: item.sequence)
    checks = _inline_checks(db, topic.id, len(lessons) * 2)
    lesson_done = set(db.scalars(
        select(LessonCompletion.lesson_id).where(
            LessonCompletion.user_id == user.id,
            LessonCompletion.lesson_id.in_([lesson.id for lesson in lessons] or [0]),
        )
    ).all())
    correct_checks = set(db.scalars(
        select(Attempt.question_id).where(
            Attempt.user_id == user.id,
            Attempt.is_correct.is_(True),
            Attempt.question_id.in_([question.id for question in checks] or [0]),
        )
    ).all())
    steps = []
    for lesson_index, lesson in enumerate(lessons):
        steps.append({
            "type": "content",
            "slug": lesson.slug,
            "title": lesson.title,
            "body_markdown": lesson.body_markdown,
            "completed": lesson.id in lesson_done,
        })
        for question in checks[lesson_index * 2:lesson_index * 2 + 2]:
            choices = load_json_list(question.choices_json)
            random.shuffle(choices)
            steps.append({
                "type": "check",
                "public_id": question.public_id,
                "prompt": question.prompt,
                "choices": choices,
                "difficulty": question.difficulty,
                "subtopic_slug": question.subtopic.slug,
                "completed_correct": question.id in correct_checks,
            })
    return {
        "slug": topic.slug,
        "title": topic.title,
        "round": topic.round,
        "phase": topic.phase,
        "steps": steps,
    }


@router.post("/learn/check")
def learn_check(payload: AttemptIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    question = db.scalar(select(Question).where(Question.public_id == payload.public_id))
    if not question or "learn-check" not in parse_list(question.tags):
        raise HTTPException(404, "Learn check not found")
    return _submit_attempt(payload, db, user)


@router.get("/planner")
def planner(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    modules = []
    for topic in _topics(db):
        tasks = [serialize_task(db, user.id, t) for t in sorted(topic.tasks, key=lambda x: x.sequence)]
        modules.append({"slug": topic.slug, "round": topic.round, "sequence": topic.sequence, "phase": topic.phase, "title": topic.title, "completed_tasks": sum(t["completed"] for t in tasks), "total_tasks": len(tasks), "tasks": tasks})
    return {"weekly_hours": user.weekly_hours, "rhythm": [{"session": x, "note": note} for x, note in [("Theory","Read and derive."),("Implementation","Code from scratch."),("Problems","Solve before explanations."),("Project","Build an end-to-end artifact."),("Mixed practice","Combine theory and code."),("Review","Repair mistakes.")]], "modules": modules}


def _task(db: Session, task_id: int):
    return db.scalar(select(StudyTask).options(selectinload(StudyTask.topic)).where(StudyTask.id == task_id))


@router.post("/planner/tasks/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = _task(db, task_id)
    if not task: raise HTTPException(404, "Task not found")
    if not db.scalar(select(TaskCompletion).where(TaskCompletion.user_id == user.id, TaskCompletion.task_id == task.id)):
        db.add(TaskCompletion(user_id=user.id, task_id=task.id)); record_activity(db, user.id, 1); db.commit()
    return serialize_task(db, user.id, task)


@router.post("/planner/tasks/{task_id}/reset")
def reset_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = _task(db, task_id)
    if not task: raise HTTPException(404, "Task not found")
    row = db.scalar(select(TaskCompletion).where(TaskCompletion.user_id == user.id, TaskCompletion.task_id == task.id))
    if row: db.delete(row); db.commit()
    return serialize_task(db, user.id, task)


@router.get("/progress")
def progress(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topics = _topics(db); attempts = db.scalars(select(Attempt).where(Attempt.user_id == user.id).order_by(Attempt.created_at.desc()).limit(20)).all()
    recent = []
    for attempt in attempts:
        q = db.get(Question, attempt.question_id)
        recent.append({"public_id": q.public_id, "prompt": q.prompt[:140], "topic": q.topic.title, "correct": attempt.is_correct, "submitted": attempt.submitted})
    return {"overall_mastery": overall_mastery(db,user,topics), "round1_progress": topic_progress(db,user,[t for t in topics if t.round==1]), "round2_progress": topic_progress(db,user,[t for t in topics if t.round==2]), "topics": [serialize_topic(db,user,t) for t in topics], "recent_attempts": recent, "missed": [x for x in recent if not x["correct"]]}


@router.get("/settings")
def get_settings(user: User = Depends(get_current_user)):
    return {"display_name": user.display_name, "weekly_hours": user.weekly_hours, "theme": user.theme}


@router.patch("/settings")
def patch_settings(payload: SettingsIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    for key, value in payload.model_dump(exclude_none=True).items(): setattr(user, key, value.strip() if isinstance(value, str) else value)
    db.commit(); return get_settings(user)


def _coding(exercise: CodingExercise, detail=False):
    result = {"slug": exercise.slug, "topic_slug": exercise.topic.slug, "title": exercise.title, "prompt": exercise.prompt, "starter_code": exercise.starter_code, "hints": load_json_list(exercise.hints_json)}
    if detail: result.update({"tests_code": exercise.tests_code, "solution_code": exercise.solution_code})
    return result


@router.get("/coding/exercises")
def coding_list(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(CodingExercise).options(selectinload(CodingExercise.topic)).order_by(CodingExercise.id)).all()
    return {"exercises": [_coding(x) for x in rows]}


@router.get("/coding/exercises/{slug}")
def coding_detail(slug: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(CodingExercise).options(selectinload(CodingExercise.topic)).where(CodingExercise.slug == slug))
    if not row: raise HTTPException(404, "Coding exercise not found")
    return _coding(row, True)


def _project_out(db, user, project, detail=False):
    progress = db.scalar(select(ProjectProgress).where(ProjectProgress.user_id == user.id, ProjectProgress.project_id == project.id))
    result = {"slug": project.slug, "round": project.round, "topic_slug": project.topic.slug, "title": project.title, "objectives": project.objectives, "completed": bool(progress and progress.completed)}
    if detail: result.update({"requirements": project.requirements, "math_notes": project.math_notes, "starter_code": project.starter_code, "tests_code": project.tests_code, "rubric": project.rubric, "hints": load_json_list(project.hints_json), "last_code": progress.last_code if progress else ""})
    return result


@router.get("/projects")
def projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Project).options(selectinload(Project.topic)).order_by(Project.round, Project.id)).all()
    return {"projects": [_project_out(db,user,x) for x in rows]}


@router.get("/projects/{slug}")
def project_detail(slug: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(Project).options(selectinload(Project.topic)).where(Project.slug == slug))
    if not row: raise HTTPException(404, "Project not found")
    return _project_out(db,user,row,True)


@router.post("/projects/{slug}/complete")
def project_complete(slug: str, payload: ProjectCompleteIn | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = db.scalar(select(Project).options(selectinload(Project.topic)).where(Project.slug == slug))
    if not project: raise HTTPException(404, "Project not found")
    payload = payload or ProjectCompleteIn()
    row = db.scalar(select(ProjectProgress).where(ProjectProgress.user_id == user.id, ProjectProgress.project_id == project.id))
    if not row: row = ProjectProgress(user_id=user.id, project_id=project.id); db.add(row)
    row.completed, row.last_code, row.updated_at = payload.completed, payload.last_code, datetime.utcnow()
    record_activity(db,user.id,1); db.commit()
    return _project_out(db,user,project,True)


@router.post("/tests/start")
def test_start(payload: TestStartIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(Question).join(Topic).where(Question.available.is_(True))
    if payload.round: query = query.where(Topic.round == payload.round)
    if payload.difficulty != "mixed": query = query.where(Question.difficulty == payload.difficulty)
    pool = list(db.scalars(query).all()); random.shuffle(pool); chosen = pool[:payload.count]
    if not chosen: raise HTTPException(404, "No questions match this test")
    row = PracticeTest(user_id=user.id, mode=payload.mode, round_filter=payload.round, difficulty=payload.difficulty, question_ids_json=json.dumps([q.id for q in chosen]), time_limit_sec=payload.time_limit_sec if payload.timed else 0)
    db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id, "question_count": len(chosen), "time_limit_sec": row.time_limit_sec, "practice_label": "Unofficial practice test"}


def _owned_test(db, user, test_id):
    row = db.scalar(select(PracticeTest).where(PracticeTest.id == test_id, PracticeTest.user_id == user.id))
    if not row: raise HTTPException(404, "Practice test not found")
    return row


@router.get("/tests/{test_id}")
def test_get(test_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = _owned_test(db,user,test_id); ids = json.loads(row.question_ids_json)
    qmap = {q.id:q for q in db.scalars(select(Question).options(selectinload(Question.topic)).where(Question.id.in_(ids))).all()}
    return {"id": row.id, "mode": row.mode, "difficulty": row.difficulty, "time_limit_sec": row.time_limit_sec, "started_at": row.started_at, "finished_at": row.finished_at, "score": row.score, "questions": [_question_out(qmap[i]) for i in ids if i in qmap], "practice_label": "Unofficial practice test"}


@router.post("/tests/{test_id}/submit")
def test_submit(test_id: int, payload: TestSubmitIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = _owned_test(db,user,test_id)
    if row.finished_at: raise HTTPException(409, "Practice test already submitted")
    ids = json.loads(row.question_ids_json); questions = db.scalars(select(Question).where(Question.id.in_(ids))).all()
    results = {q.public_id: grade_submission(q,payload.answers.get(q.public_id,"")) for q in questions}
    row.answers_json=json.dumps(payload.answers); row.finished_at=datetime.utcnow(); row.score=100*sum(results.values())/len(questions)
    for q in questions: db.add(Attempt(user_id=user.id, question_id=q.id, submitted=payload.answers.get(q.public_id,""), is_correct=results[q.public_id]))
    record_activity(db,user.id,1); db.commit()
    return {"id": row.id, "score": row.score, "results": results, "practice_label": "Unofficial practice test"}


@router.post("/tutor/chat")
def tutor_chat(payload: TutorChatIn, user: User = Depends(get_current_user)):
    if settings.openai_api_key:
        messages = [{"role":"system","content":"You are a Socratic tutor for unofficial AI Olympiad practice. Ask guiding questions and never claim official affiliation."}] + [m.model_dump() for m in payload.messages]
        response = httpx.post(f"{settings.openai_base_url.rstrip('/')}/chat/completions", headers={"Authorization":f"Bearer {settings.openai_api_key}"}, json={"model":settings.openai_model,"messages":messages}, timeout=30)
        if response.is_error: raise HTTPException(502, "Tutor provider unavailable")
        content = response.json()["choices"][0]["message"]["content"]
    else:
        prompt = payload.messages[-1].content
        content = f"Let’s work through this as unofficial practice. What definitions, tensor shapes, or assumptions in “{prompt[:180]}” can you state first? Then try one small numerical case; tell me where your reasoning becomes uncertain."
    return {"role":"assistant","content":content,"practice_label":"Unofficial practice tutor"}
