"""
Pytest configuration — in-memory SQLite test database.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# import all models so they register with Base
import app.models.models  # noqa: F401

from app.database import Base, get_db
from app.main import app

# use a file-based SQLite for tests (in-memory has issues across connections)
TEST_DB = "sqlite:///./test_queueflow.db"

engine_test = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    # create tables fresh for every test
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client(reset_db):  # explicit dependency ensures tables exist first
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
def manager_data():
    return {
        "email": "test@example.com",
        "password": "secret123",
        "full_name": "Test Manager",
    }


@pytest.fixture
def auth_client(client, manager_data):
    """Client with an authenticated manager."""
    client.post("/api/auth/register", json=manager_data)
    resp = client.post(
        "/api/auth/login",
        json={"email": manager_data["email"], "password": manager_data["password"]},
    )
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
