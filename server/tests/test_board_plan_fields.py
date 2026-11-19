import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db, limiter
from app.models import Board, User


@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-jwt-secret-key-at-least-32-bytes",
    })
    limiter.reset()

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_board_can_store_plan_details(client):
    with client.application.app_context():
        user = User(username="planner", email="planner@example.com")
        user.set_password("secret")
        db.session.add(user)
        db.session.commit()

        board = Board(
            title="Ceramic Mug Project",
            hobby_type="Ceramics",
            description="A weekend craft board",
            user_id=user.id,
            materials="Clay, glaze",
            notes="Need a kiln schedule"
        )
        db.session.add(board)
        db.session.commit()
        board_id = board.id

    response = client.post(
        "/api/login",
        json={"email": "planner@example.com", "password": "secret"},
    )
    token = response.get_json()["access_token"]

    response = client.get(
        f"/api/boards/{board_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    data = response.get_json()["board"]
    assert data["materials"] == "Clay, glaze"
    assert data["notes"] == "Need a kiln schedule"


def test_board_target_date_can_be_created_updated_and_cleared(client):
    signup_response = client.post(
        "/api/signup",
        json={"username": "dateplanner", "email": "dates@example.com", "password": "secret123"},
    )
    token = signup_response.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/boards",
        json={"title": "Garden Bed", "hobby_type": "Gardening", "target_date": "2027-05-01"},
        headers=headers,
    )

    assert create_response.status_code == 201
    board_id = create_response.get_json()["board"]["id"]
    assert create_response.get_json()["board"]["target_date"] == "2027-05-01"

    update_response = client.patch(
        f"/api/boards/{board_id}",
        json={"target_date": "2027-05-15"},
        headers=headers,
    )

    assert update_response.status_code == 200
    assert update_response.get_json()["board"]["target_date"] == "2027-05-15"

    clear_response = client.patch(
        f"/api/boards/{board_id}",
        json={"target_date": ""},
        headers=headers,
    )

    assert clear_response.status_code == 200
    assert clear_response.get_json()["board"]["target_date"] is None


def test_board_target_date_rejects_invalid_date(client):
    signup_response = client.post(
        "/api/signup",
        json={"username": "invaliddate", "email": "invaliddate@example.com", "password": "secret123"},
    )
    token = signup_response.get_json()["access_token"]

    response = client.post(
        "/api/boards",
        json={"title": "Garden Bed", "hobby_type": "Gardening", "target_date": "2027-02-30"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "target date" in response.get_json()["error"].lower()
