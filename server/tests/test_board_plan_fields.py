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
