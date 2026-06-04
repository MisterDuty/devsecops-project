import pytest

from app.app import create_app, db


@pytest.fixture()
def client():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "RATELIMIT_DEFAULT": "1000 per minute",
        }
    )
    with app.app_context():
        db.drop_all()
        db.create_all()

    with app.test_client() as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert "X-Content-Type-Options" in response.headers


def test_create_update_delete_task(client):
    created = client.post("/api/tasks", json={"title": "Scanner l'image Docker"})

    assert created.status_code == 201
    task_id = created.get_json()["id"]

    updated = client.put(f"/api/tasks/{task_id}", json={"status": "done"})
    assert updated.status_code == 200
    assert updated.get_json()["status"] == "done"

    deleted = client.delete(f"/api/tasks/{task_id}")
    assert deleted.status_code == 204


def test_reject_invalid_payload(client):
    response = client.post("/api/tasks", json={"title": "", "priority": "urgent"})

    assert response.status_code == 400
    assert "title" in response.get_json()["errors"]
    assert "priority" in response.get_json()["errors"]


def test_sanitize_html_input(client):
    response = client.post("/api/tasks", json={"title": "<script>alert(1)</script>"})

    assert response.status_code == 201
    assert response.get_json()["title"] == "&lt;script&gt;alert(1)&lt;/script&gt;"
