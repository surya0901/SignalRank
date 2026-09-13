from fastapi.testclient import TestClient

from app.db import get_db
from app.main import app
from app.seed import import_archive


def test_live_endpoint():
    with TestClient(app) as client:
        assert client.get("/health/live").json() == {"status": "ok"}


def test_readiness_and_actual_dataset_counts(db, archive):
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as client:
            assert client.get("/health/ready").status_code == 503
            assert client.get("/api/dataset").status_code == 503
            import_archive(db, archive, "fixture")
            db.commit()
            assert client.get("/health/ready").status_code == 200
            result = client.get("/api/dataset").json()
            assert result["movies"] == 2
            assert result["ratings"] == 2
            assert result["users"] == 2
            assert result["genres"] == 2
    finally:
        app.dependency_overrides.clear()
