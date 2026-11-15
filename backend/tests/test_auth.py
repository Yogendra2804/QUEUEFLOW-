"""
Auth endpoint tests.
"""


def test_register(client, manager_data):
    r = client.post("/api/auth/register", json=manager_data)
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == manager_data["email"]
    assert data["full_name"] == manager_data["full_name"]
    assert "hashed_password" not in data


def test_register_duplicate(client, manager_data):
    client.post("/api/auth/register", json=manager_data)
    r = client.post("/api/auth/register", json=manager_data)
    assert r.status_code == 400


def test_login_success(client, manager_data):
    client.post("/api/auth/register", json=manager_data)
    r = client.post(
        "/api/auth/login",
        json={"email": manager_data["email"], "password": manager_data["password"]},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client, manager_data):
    client.post("/api/auth/register", json=manager_data)
    r = client.post(
        "/api/auth/login",
        json={"email": manager_data["email"], "password": "WRONG"},
    )
    assert r.status_code == 401


def test_login_nonexistent_user(client):
    r = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "doesntmatter"},
    )
    assert r.status_code == 401


def test_me_requires_auth(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_authenticated(auth_client):
    r = auth_client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "test@example.com"


def test_short_password(client):
    r = client.post(
        "/api/auth/register",
        json={"email": "x@x.com", "password": "12", "full_name": "X"},
    )
    assert r.status_code == 422
