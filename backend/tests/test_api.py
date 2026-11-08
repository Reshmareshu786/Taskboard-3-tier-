import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app


def client():
    return app.test_client()


def test_health():
    r = client().get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_metrics_exposed():
    c = client()
    c.get("/health")
    r = c.get("/metrics")
    assert r.status_code == 200
    assert b"http_requests_total" in r.data


def test_create_task_validation():
    r = client().post("/api/tasks", json={"title": "  "})
    assert r.status_code == 400
