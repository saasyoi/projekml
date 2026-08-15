from unittest.mock import patch

from api.ai import AIServiceError


def _register_and_login(client, email="chatuser@example.com"):
    res = client.post("/api/auth/register", json={"email": email, "name": "Budi", "password": "password123"})
    assert res.status_code == 200
    return res.json()


def _agent_result(reply="Ini balasan aman.", matched_scenario=None, suggested_quiz=None, official_contact=None):
    return {
        "reply": reply,
        "matched_scenario": matched_scenario,
        "suggested_quiz": suggested_quiz,
        "official_contact": official_contact,
    }


def test_chat_requires_auth(client):
    res = client.post("/api/chat", data={"message": "halo"})
    assert res.status_code == 401


def test_chat_rejects_empty_message_and_no_file(client):
    _register_and_login(client)
    res = client.post("/api/chat", data={"message": ""})
    assert res.status_code == 400


def test_chat_text_message_happy_path(client):
    _register_and_login(client)
    with patch("main.run_scam_agent", return_value=_agent_result(reply="Halo, ada yang bisa dibantu?")):
        res = client.post("/api/chat", data={"message": "halo, ini penipuan bukan?"})
    assert res.status_code == 200
    body = res.json()
    assert body["reply"] == "Halo, ada yang bisa dibantu?"
    assert body["status"] is None


def test_chat_message_persists_in_history(client):
    _register_and_login(client)
    with patch("main.run_scam_agent", return_value=_agent_result(reply="Balasan bot")):
        client.post("/api/chat", data={"message": "pesan pertama"})

    res = client.get("/api/history/chat")
    assert res.status_code == 200
    history = res.json()
    assert len(history) == 2  # pesan user + balasan model
    assert history[0]["content"] == "pesan pertama"
    assert history[1]["content"] == "Balasan bot"


def test_chat_ai_service_error_returns_503(client):
    _register_and_login(client)
    with patch("main.run_scam_agent", side_effect=AIServiceError("Gemini sedang down")):
        res = client.post("/api/chat", data={"message": "halo"})
    assert res.status_code == 503


def test_chat_rejects_bad_image_content_type(client):
    _register_and_login(client)
    res = client.post(
        "/api/chat",
        data={"message": ""},
        files={"file": ("note.txt", b"bukan gambar", "text/plain")},
    )
    assert res.status_code == 400


def test_chat_rejects_oversized_image(client):
    _register_and_login(client)
    big_bytes = b"\xff" * (5 * 1024 * 1024 + 1)
    res = client.post(
        "/api/chat",
        data={"message": ""},
        files={"file": ("big.png", big_bytes, "image/png")},
    )
    assert res.status_code == 413


def test_chat_image_with_no_readable_text(client):
    _register_and_login(client)
    with patch("main.analyze_image_with_gemini", return_value="NO_TEXT_FOUND"):
        res = client.post(
            "/api/chat",
            data={"message": ""},
            files={"file": ("photo.png", b"\x89PNG\r\n fake bytes", "image/png")},
        )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "no_content"


def test_chat_image_flags_danger_when_scenario_matched(client):
    _register_and_login(client)
    with patch("main.analyze_image_with_gemini", return_value="Transfer sekarang atau rekening diblokir"), \
         patch("main.run_scam_agent", return_value=_agent_result(matched_scenario={"id": "cs_bank_palsu"})):
        res = client.post(
            "/api/chat",
            data={"message": ""},
            files={"file": ("photo.png", b"\x89PNG\r\n fake bytes", "image/png")},
        )
    assert res.status_code == 200
    assert res.json()["status"] == "danger"


def test_clear_chat_history(client):
    _register_and_login(client)
    with patch("main.run_scam_agent", return_value=_agent_result()):
        client.post("/api/chat", data={"message": "halo"})

    assert len(client.get("/api/history/chat").json()) == 2

    res = client.delete("/api/chat/history")
    assert res.status_code == 200
    assert client.get("/api/history/chat").json() == []


def test_chat_text_rate_limited_after_max_messages(client):
    _register_and_login(client)
    with patch("main.run_scam_agent", return_value=_agent_result()):
        for _ in range(30):
            res = client.post("/api/chat", data={"message": "halo"})
            assert res.status_code == 200
        res = client.post("/api/chat", data={"message": "halo lagi"})
    assert res.status_code == 429
