import os

os.environ["DATABASE_URL"] = "sqlite:///./test_ultra_opencart.db"
os.environ["SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_login_and_me():
    email = "test@example.com"
    password = "StrongPass123!"

    register = client.post("/auth/register", json={"email": email, "password": password})
    assert register.status_code in (201, 409)

    login = client.post("/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email
