import pytest
from fastapi.testclient import TestClient

from app import api
from app.db import get_db
from app.main import app


@pytest.fixture
def clients(db, monkeypatch):
    app.dependency_overrides[get_db] = lambda: db
    api.limiter.clear()
    monkeypatch.setattr(
        api,
        "load_catalog",
        lambda: {
            "movies": [
                {
                    "id": 1,
                    "title": "Example",
                    "genres": ["Drama"],
                    "neighbors": [],
                    "quality": 0.8,
                    "count": 5,
                    "mean": 4,
                }
            ]
        },
    )
    with TestClient(app) as first, TestClient(app) as second:
        yield first, second
    app.dependency_overrides.clear()


def test_session_required_and_isolated(clients):
    first, second = clients
    assert first.get("/api/me").status_code == 401
    assert first.post("/api/auth/demo").status_code == 200
    assert second.post("/api/auth/demo").status_code == 200
    state = {"ratings": {"1": 3.5}, "liked": [1], "saved": [1], "genres": ["Drama"]}
    assert first.put("/api/me", json=state).status_code == 200
    assert first.get("/api/me").json() == state
    assert second.get("/api/me").json() != state
    assert "HttpOnly" in first.post("/api/auth/demo").headers.get("set-cookie", "") or first.cookies


def test_cross_origin_mutation_denied(clients):
    first, _ = clients
    assert (
        first.post("/api/auth/demo", headers={"Origin": "https://untrusted.example"}).status_code
        == 403
    )


def test_invalid_ratings_and_unknown_movies_rejected(clients):
    first, _ = clients
    first.post("/api/auth/demo")
    assert first.put("/api/me", json={"ratings": {"1": 3.3}}).status_code == 422
    assert first.put("/api/me", json={"saved": [999999]}).status_code == 422


def test_logout_revokes_session(clients):
    first, _ = clients
    first.post("/api/auth/demo")
    assert first.delete("/api/auth/session").status_code == 204
    assert first.get("/api/me").status_code == 401


def test_search_and_pagination(clients):
    first, _ = clients
    assert first.get("/api/movies?q=example").json()["total"] == 1
    assert first.get("/api/movies?offset=1").json()["items"] == []
    assert first.get("/api/movies?limit=200").status_code == 422
