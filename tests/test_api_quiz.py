def _register_and_login(client, email="quizuser@example.com"):
    res = client.post("/api/auth/register", json={"email": email, "name": "Budi", "password": "password123"})
    assert res.status_code == 200
    return res.json()


def test_topics_are_public(client):
    res = client.get("/api/topics")
    assert res.status_code == 200
    keys = {t["key"] for t in res.json()}
    assert {"apk", "link", "sosial"}.issubset(keys)


def test_get_quiz_requires_auth(client):
    res = client.get("/api/quiz/apk/dasar")
    assert res.status_code == 401


def test_get_quiz_dasar(client):
    _register_and_login(client)
    res = client.get("/api/quiz/apk/dasar")
    assert res.status_code == 200
    body = res.json()
    assert len(body["questions"]) == 3
    for q in body["questions"]:
        assert "correct" not in q  # never leak the answer to the client


def test_advanced_level_locked_until_basic_passed(client):
    _register_and_login(client)
    res = client.get("/api/quiz/apk/lanjutan")
    assert res.status_code == 403


def test_unknown_topic_404(client):
    _register_and_login(client)
    res = client.get("/api/quiz/does-not-exist/dasar")
    assert res.status_code == 404


def test_answer_reports_correctness(client):
    _register_and_login(client)
    res = client.post("/api/quiz/answer", json={"topic": "apk", "level": "dasar", "index": 0, "letter": "B"})
    assert res.status_code == 200
    body = res.json()
    assert body["correct"] is True
    assert body["correct_letter"] == "B"


def test_finish_quiz_passing_awards_badge_and_unlocks_next(client):
    _register_and_login(client)
    res = client.post("/api/quiz/finish", json={"topic": "apk", "level": "dasar", "correct_count": 3, "total": 3})
    assert res.status_code == 200
    body = res.json()
    assert body["percent"] == 100
    assert body["passed"] is True
    assert body["unlocked_next"] is True
    assert body["badge_earned"]

    # Advanced level should now be reachable
    res2 = client.get("/api/quiz/apk/lanjutan")
    assert res2.status_code == 200


def test_finish_quiz_failing_does_not_unlock_next(client):
    _register_and_login(client)
    res = client.post("/api/quiz/finish", json={"topic": "apk", "level": "dasar", "correct_count": 1, "total": 3})
    body = res.json()
    assert body["passed"] is False
    assert body["badge_earned"] is None

    res2 = client.get("/api/quiz/apk/lanjutan")
    assert res2.status_code == 403


def test_finish_quiz_rejects_impossible_score(client):
    _register_and_login(client)
    res = client.post("/api/quiz/finish", json={"topic": "apk", "level": "dasar", "correct_count": 5, "total": 3})
    assert res.status_code == 422


def test_dashboard_reflects_progress(client):
    _register_and_login(client)
    client.post("/api/quiz/finish", json={"topic": "apk", "level": "dasar", "correct_count": 3, "total": 3})
    res = client.get("/api/dashboard")
    body = res.json()
    assert body["user_record"]["total_score"] > 0
    assert body["user_record"]["progress"]["apk"]["dasar"]["passed"] is True


def test_quiz_history_records_attempt(client):
    _register_and_login(client)
    client.post("/api/quiz/finish", json={"topic": "apk", "level": "dasar", "correct_count": 3, "total": 3})
    res = client.get("/api/history/quiz")
    assert res.status_code == 200
    history = res.json()
    assert len(history) == 1
    assert history[0]["topic"] == "apk"
    assert history[0]["passed"] is True
