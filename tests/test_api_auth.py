def _register(client, email="user@example.com", password="password123", name="Budi"):
    return client.post("/api/auth/register", json={"email": email, "name": name, "password": password})


def test_register_returns_user(client):
    res = _register(client)
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "user@example.com"
    assert "id" in body
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_sets_session_cookie(client):
    res = _register(client)
    assert "fs_session" in res.cookies


def test_register_duplicate_email_rejected(client):
    _register(client)
    res = _register(client)
    assert res.status_code == 400


def test_me_requires_session(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_works_after_register(client):
    _register(client)
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["email"] == "user@example.com"


def test_login_wrong_password_rejected(client):
    _register(client)
    res = client.post("/api/auth/login", json={"email": "user@example.com", "password": "wrongpass"})
    assert res.status_code == 401


def test_login_correct_password(client):
    _register(client)
    client.cookies.clear()
    res = client.post("/api/auth/login", json={"email": "user@example.com", "password": "password123"})
    assert res.status_code == 200


def test_login_unknown_email_rejected(client):
    res = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert res.status_code == 401


def test_logout_clears_session(client):
    _register(client)
    assert client.get("/api/auth/me").status_code == 200
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401
