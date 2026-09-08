import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from app.models import Board, User


@pytest.fixture
def client():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        JWT_SECRET_KEY="test-jwt-secret-key-at-least-32-bytes",
    )

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def setup_user_board(client):
    with client.application.app_context():
        user = User(username="tasker", email="tasker@example.com")
        user.set_password("secret")
        db.session.add(user)
        db.session.commit()

        board = Board(
            title="Model Train Build",
            hobby_type="Modeling",
            description="Weekend project",
            user_id=user.id,
        )
        db.session.add(board)
        db.session.commit()
        board_id = board.id

    login_response = client.post(
        "/api/login",
        json={"email": "tasker@example.com", "password": "secret"},
    )
    token = login_response.get_json()["access_token"]

    return board_id, token


def test_create_task_rejects_invalid_status_and_priority(client):
    board_id, token = setup_user_board(client)

    response = client.post(
        f"/api/boards/{board_id}/tasks",
        json={
            "title": "Prime and paint",
            "status": "Started",
            "priority": "Urgent",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] in {"Invalid task status", "Invalid task priority"}


def test_update_task_rejects_invalid_priority(client):
    board_id, token = setup_user_board(client)

    create_response = client.post(
        f"/api/boards/{board_id}/tasks",
        json={"title": "Cut plywood"},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = create_response.get_json()["task"]["id"]

    update_response = client.patch(
        f"/api/tasks/{task_id}",
        json={"priority": "Critical"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert update_response.status_code == 400
    payload = update_response.get_json()
    assert payload["error"] == "Invalid task priority"
    assert sorted(payload["allowed_values"]) == ["High", "Low", "Medium"]
