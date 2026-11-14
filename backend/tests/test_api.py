def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_round_2_is_unlocked(client):
    payload = client.get("/api/topics").json()
    rounds = {track["round"] for track in payload["tracks"]}
    assert 1 in rounds
    assert 2 in rounds
    attention = next(
        module
        for track in payload["tracks"]
        for module in track["modules"]
        if module["slug"] == "attention-mechanisms"
    )
    assert attention["round"] == 2
    assert "lock" not in attention["mastery_status"]


def test_modules_have_no_estimated_times_or_calendar_dates(client):
    payload = client.get("/api/topics").json()
    for track in payload["tracks"]:
        for module in track["modules"]:
            assert "2026" not in module["title"]
            assert "2027" not in module["summary"]
            assert "Sep" not in module["title"]
            assert "estimated_hours" not in module
            assert "estimated_minutes" not in module


def test_dashboard_and_week_1_lesson(client):
    dash = client.get("/api/dashboard").json()
    assert dash["streak"] == 0
    assert dash["stats"]["questions"] >= 8
    assert dash["continue_lesson"]["slug"] == "python-colab-markdown-core"

    lesson = client.get("/api/lessons/python-colab-markdown-core").json()
    assert "Common mistakes" in lesson["body_markdown"]
    done = client.post("/api/lessons/python-colab-markdown-core/complete")
    assert done.status_code == 200
    again = client.get("/api/lessons/python-colab-markdown-core").json()
    assert again["completed"] is True

    dash2 = client.get("/api/dashboard").json()
    assert dash2["streak"] == 1


def test_practice_flow_grades_and_tracks_mastery(client):
    meta = client.get("/api/practice/meta").json()
    python_meta = next(topic for topic in meta["topics"] if topic["slug"] == "python-colab-markdown")
    subtopic = python_meta["subtopics"][0]
    assert subtopic["counts"] == {"easy": 50, "medium": 100, "hard": 50}

    question = client.get(
        f"/api/practice/next?topic=python-colab-markdown&subtopic={subtopic['slug']}&difficulty=easy"
    ).json()
    assert question["practice_label"] == "Unofficial practice question"
    assert question["public_id"].startswith("R1T01-")
    assert question["subtopic_slug"] == subtopic["slug"]

    wrong = client.post(
        "/api/practice/attempt",
        json={"public_id": question["public_id"], "submitted": "__wrong__", "hints_used": 1},
    ).json()
    assert wrong["is_correct"] is False

    right = client.post(
        "/api/practice/attempt",
        json={"public_id": question["public_id"], "submitted": wrong["correct_answer"], "hints_used": 0},
    ).json()
    assert right["is_correct"] is True
    assert right["theory_score"] > 0

    progress = client.get("/api/progress").json()
    python = next(topic for topic in progress["topics"] if topic["slug"] == "python-colab-markdown")
    assert python["theory_attempts"] if False else python["theory_score"] > 0


def test_learn_modules_interleave_content_and_checks(client):
    groups = client.get("/api/learn/modules").json()["groups"]
    python = next(
        module
        for group in groups
        for module in group["modules"]
        if module["slug"] == "python-colab-markdown"
    )
    assert python["progress"]["lessons_done"] == 0
    detail = client.get("/api/learn/modules/python-colab-markdown").json()
    assert [step["type"] for step in detail["steps"][:3]] == ["content", "check", "check"]
    check = detail["steps"][1]
    wrong = client.post(
        "/api/learn/check",
        json={"public_id": check["public_id"], "submitted": "__wrong__"},
    ).json()
    right = client.post(
        "/api/learn/check",
        json={"public_id": check["public_id"], "submitted": wrong["correct_answer"]},
    ).json()
    assert right["is_correct"] is True
    detail_after = client.get("/api/learn/modules/python-colab-markdown").json()
    assert detail_after["steps"][1]["completed_correct"] is True


def test_planner_completes_tasks(client):
    plan = client.get("/api/planner").json()
    assert plan["weekly_hours"] == 11
    assert len(plan["rhythm"]) == 6
    first = plan["modules"][0]
    assert first["slug"] == "python-colab-markdown"
    task_id = first["tasks"][0]["id"]
    done = client.post(f"/api/planner/tasks/{task_id}/complete").json()
    assert done["completed"] is True
    reset = client.post(f"/api/planner/tasks/{task_id}/reset").json()
    assert reset["completed"] is False


def test_settings_update(client):
    updated = client.patch("/api/settings", json={"display_name": "Alex", "weekly_hours": 8, "theme": "dark"}).json()
    assert updated["display_name"] == "Alex"
    assert updated["weekly_hours"] == 8
    assert updated["theme"] == "dark"


def test_coding_projects_and_test_flow(client):
    exercises = client.get("/api/coding/exercises").json()["exercises"]
    assert len(exercises) >= 12
    assert client.get(f"/api/coding/exercises/{exercises[0]['slug']}").status_code == 200

    projects = client.get("/api/projects").json()["projects"]
    assert len(projects) == 6
    done = client.post(f"/api/projects/{projects[0]['slug']}/complete", json={"last_code": "# done"}).json()
    assert done["completed"] is True

    started = client.post("/api/tests/start", json={"mode": "practice", "round": 2, "difficulty": "mixed", "count": 3, "timed": True, "time_limit_sec": 300}).json()
    test = client.get(f"/api/tests/{started['id']}").json()
    assert len(test["questions"]) == 3
    answers = {question["public_id"]: "" for question in test["questions"]}
    submitted = client.post(f"/api/tests/{started['id']}/submit", json={"answers": answers}).json()
    assert submitted["practice_label"] == "Unofficial practice test"


def test_auth_required_and_tutor_fallback(client):
    auth = client.headers.pop("Authorization")
    assert client.get("/api/topics").status_code == 401
    client.headers["Authorization"] = auth
    response = client.post("/api/tutor/chat", json={"messages": [{"role": "user", "content": "How does PCA work?"}]})
    assert response.status_code == 200
    assert "unofficial practice" in response.json()["content"].lower()
