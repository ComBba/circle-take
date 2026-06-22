import os
import tempfile

import pytest
from app import auth
from app.deps import get_store
from app.main import app
from app.store import Store
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app.dependency_overrides[get_store] = lambda: Store(path)
    yield TestClient(app)
    app.dependency_overrides.clear()
    os.remove(path)


def _register(c, email="luna@circle.take", pw="password123"):
    return c.post("/api/auth/register", json={"email": email, "password": pw})


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_returns_token(client):
    r = _register(client)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and len(body["access_token"]) > 20


def test_register_duplicate_email_409(client):
    _register(client)
    assert _register(client).status_code == 409


def test_register_short_password_422(client):
    r = client.post("/api/auth/register", json={"email": "x@y.com", "password": "short"})
    assert r.status_code == 422


def test_register_invalid_email_422(client):
    r = client.post("/api/auth/register", json={"email": "not-an-email", "password": "password123"})
    assert r.status_code == 422


def test_login_ok_and_wrong_password(client):
    _register(client)
    ok = client.post("/api/auth/login", json={"email": "luna@circle.take", "password": "password123"})
    assert ok.status_code == 200 and ok.json()["access_token"]
    bad = client.post("/api/auth/login", json={"email": "luna@circle.take", "password": "WRONG-pass1"})
    assert bad.status_code == 401


def test_login_unknown_email_401(client):
    r = client.post("/api/auth/login", json={"email": "ghost@circle.take", "password": "password123"})
    assert r.status_code == 401


def test_me_requires_token(client):
    token = _register(client).json()["access_token"]
    assert client.get("/api/auth/me").status_code == 401
    me = client.get("/api/auth/me", headers=_bearer(token))
    assert me.status_code == 200 and me.json()["email"] == "luna@circle.take"


def test_me_bad_token_401(client):
    assert client.get("/api/auth/me", headers=_bearer("not.a.jwt")).status_code == 401


def test_me_expired_token_401(client):
    expired = auth.create_access_token("us-whoever", ttl_minutes=-1)
    assert client.get("/api/auth/me", headers=_bearer(expired)).status_code == 401


def test_episodes_require_auth(client):
    # No token -> 401, not 403.
    assert client.post("/api/episodes", json={"title": "X"}).status_code == 401
    assert client.get("/api/episodes").status_code == 401


def test_password_is_hashed_not_plaintext(client):
    _register(client)
    store = app.dependency_overrides[get_store]()
    user = store.get_user_by_email("luna@circle.take")
    assert user["password_hash"] != "password123"
    assert auth.verify_password("password123", user["password_hash"])


def test_per_user_episode_isolation(client):
    a = _register(client, "a@circle.take").json()["access_token"]
    b = _register(client, "b@circle.take").json()["access_token"]
    eid = client.post("/api/episodes", json={"title": "A-owned"}, headers=_bearer(a)).json()["episode_id"]
    # owner sees it
    assert client.get(f"/api/episodes/{eid}", headers=_bearer(a)).status_code == 200
    # other user gets 404 (no existence leak), and cannot mutate it
    assert client.get(f"/api/episodes/{eid}", headers=_bearer(b)).status_code == 404
    assert client.post(f"/api/episodes/{eid}/generate", headers=_bearer(b)).status_code == 404
    # B's list is empty, A's has one
    assert client.get("/api/episodes", headers=_bearer(b)).json() == []
    assert len(client.get("/api/episodes", headers=_bearer(a)).json()) == 1
