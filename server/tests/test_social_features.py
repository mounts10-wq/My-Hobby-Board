import sys
from io import BytesIO
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from app.models import Board, BoardUpdate, User


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


def _signup_and_auth(client, username, email, password="secret123"):
    response = client.post(
        "/api/signup",
        json={"username": username, "email": email, "password": password},
    )
    assert response.status_code == 201
    payload = response.get_json()
    return payload["access_token"], payload["user"]["id"]


def test_follow_board_and_feed_include_public_updates(client):
    owner_token, owner_user_id = _signup_and_auth(client, "owner", "owner@example.com")
    follower_token, _ = _signup_and_auth(client, "follower", "follower@example.com")

    create_board_response = client.post(
        "/api/boards",
        json={
            "title": "Urban Gardening",
            "hobby_type": "Gardening",
            "description": "Balcony project",
            "is_public": True,
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create_board_response.status_code == 201
    board_id = create_board_response.get_json()["board"]["id"]

    create_update_response = client.post(
        f"/api/boards/{board_id}/updates",
        json={"content": "Seedlings are sprouting!", "media_url": "https://example.com/video"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert create_update_response.status_code == 201

    follow_response = client.post(
        f"/api/boards/{board_id}/follow",
        headers={"Authorization": f"Bearer {follower_token}"},
    )
    assert follow_response.status_code == 201

    feed_response = client.get(
        "/api/feed",
        headers={"Authorization": f"Bearer {follower_token}"},
    )

    assert feed_response.status_code == 200
    updates = feed_response.get_json()["updates"]
    assert any(update["content"] == "Seedlings are sprouting!" for update in updates)
    target = next(update for update in updates if update["content"] == "Seedlings are sprouting!")
    assert target["board_title"] == "Urban Gardening"
    assert target["media_url"] == "https://example.com/video"


def test_following_one_board_does_not_follow_all_user_boards(client):
    owner_token, _ = _signup_and_auth(client, "james", "james@example.com")
    follower_token, _ = _signup_and_auth(client, "felina", "felina@example.com")

    bronco_board_response = client.post(
        "/api/boards",
        json={"title": "Bronco", "hobby_type": "Cars", "is_public": True},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    bronco_board_id = bronco_board_response.get_json()["board"]["id"]

    garden_board_response = client.post(
        "/api/boards",
        json={"title": "Garden", "hobby_type": "Gardening", "is_public": True},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    garden_board_id = garden_board_response.get_json()["board"]["id"]

    client.post(
        f"/api/boards/{bronco_board_id}/updates",
        json={"content": "Rebuilt the front suspension."},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    client.post(
        f"/api/boards/{garden_board_id}/updates",
        json={"content": "Planted tomatoes this morning."},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    follow_response = client.post(
        f"/api/boards/{bronco_board_id}/follow",
        headers={"Authorization": f"Bearer {follower_token}"},
    )
    assert follow_response.status_code == 201

    feed_response = client.get(
        "/api/feed",
        headers={"Authorization": f"Bearer {follower_token}"},
    )

    assert feed_response.status_code == 200
    updates = feed_response.get_json()["updates"]
    feed_contents = {item["content"] for item in updates}
    assert "Rebuilt the front suspension." in feed_contents
    assert "Planted tomatoes this morning." not in feed_contents

    following_boards_response = client.get(
        "/api/me/following/boards",
        headers={"Authorization": f"Bearer {follower_token}"},
    )
    assert following_boards_response.status_code == 200
    boards = following_boards_response.get_json()["boards"]
    assert len(boards) == 1
    assert boards[0]["title"] == "Bronco"


def test_update_comments_allow_viewers_on_public_board(client):
    owner_token, _ = _signup_and_auth(client, "builder", "builder@example.com")
    commenter_token, _ = _signup_and_auth(client, "helper", "helper@example.com")

    create_board_response = client.post(
        "/api/boards",
        json={"title": "Model Rocket", "hobby_type": "STEM", "is_public": True},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    board_id = create_board_response.get_json()["board"]["id"]

    create_update_response = client.post(
        f"/api/boards/{board_id}/updates",
        json={"content": "Installed the recovery system."},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    update_id = create_update_response.get_json()["update"]["id"]

    comment_response = client.post(
        f"/api/updates/{update_id}/comments",
        json={"content": "Nice work. Have you tested wind conditions?"},
        headers={"Authorization": f"Bearer {commenter_token}"},
    )

    assert comment_response.status_code == 201
    assert comment_response.get_json()["comment"]["username"] == "helper"

    get_comments_response = client.get(
        f"/api/updates/{update_id}/comments",
        headers={"Authorization": f"Bearer {commenter_token}"},
    )
    assert get_comments_response.status_code == 200
    comments = get_comments_response.get_json()["comments"]
    assert len(comments) == 1
    assert comments[0]["content"] == "Nice work. Have you tested wind conditions?"


def test_discover_boards_filters_public_results(client):
    owner_token, _ = _signup_and_auth(client, "maker", "maker@example.com")
    viewer_token, _ = _signup_and_auth(client, "viewer", "viewer@example.com")

    public_response = client.post(
        "/api/boards",
        json={"title": "Wood Lathe Bowl", "hobby_type": "Woodworking", "is_public": True},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert public_response.status_code == 201

    private_response = client.post(
        "/api/boards",
        json={"title": "Private Sketches", "hobby_type": "Drawing", "is_public": False},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert private_response.status_code == 201

    discover_response = client.get(
        "/api/discover/boards?q=Wood&hobby=wood",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert discover_response.status_code == 200
    boards = discover_response.get_json()["boards"]
    assert len(boards) == 1
    assert boards[0]["title"] == "Wood Lathe Bowl"
    assert boards[0]["owner_username"] == "maker"


def test_uploaded_media_is_only_accessible_to_owner_or_followers(client):
    owner_token, _ = _signup_and_auth(client, "owner", "owner@example.com")
    follower_token, _ = _signup_and_auth(client, "follower", "follower@example.com")
    viewer_token, _ = _signup_and_auth(client, "viewer", "viewer@example.com")

    create_board_response = client.post(
        "/api/boards",
        json={"title": "Studio Updates", "hobby_type": "Photography", "is_public": True},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    board_id = create_board_response.get_json()["board"]["id"]

    upload_response = client.post(
        f"/api/boards/{board_id}/updates",
        data={
            "content": "Shared a new shot",
            "media_file": (BytesIO(b"fake-image-bytes"), "photo.png"),
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert upload_response.status_code == 201
    media_url = upload_response.get_json()["update"]["media_url"]
    filename = media_url.split("/")[-1]

    owner_media_response = client.get(
        f"/api/uploads/{filename}?token={owner_token}",
    )
    assert owner_media_response.status_code == 200

    client.post(
        f"/api/boards/{board_id}/follow",
        headers={"Authorization": f"Bearer {follower_token}"},
    )

    follower_media_response = client.get(
        f"/api/uploads/{filename}?token={follower_token}",
    )
    assert follower_media_response.status_code == 200

    viewer_media_response = client.get(
        f"/api/uploads/{filename}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_media_response.status_code == 403


def test_uploading_media_file_to_board_update_saves_attachment(client):
    owner_token, _ = _signup_and_auth(client, "uploader", "uploader@example.com")

    create_board_response = client.post(
        "/api/boards",
        json={"title": "Photo Log", "hobby_type": "Photography", "is_public": True},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    board_id = create_board_response.get_json()["board"]["id"]

    response = client.post(
        f"/api/boards/{board_id}/updates",
        data={
            "content": "Uploaded a new photo",
            "media_file": (BytesIO(b"fake-image-bytes"), "photo.png"),
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 201
    payload = response.get_json()["update"]
    assert payload["content"] == "Uploaded a new photo"
    assert payload["media_url"].startswith("/api/uploads/")


def test_discover_boards_requires_search_terms_and_excludes_own_and_followed_boards(client):
    owner_token, _ = _signup_and_auth(client, "owner", "owner@example.com")
    viewer_token, _ = _signup_and_auth(client, "viewer", "viewer@example.com")
    other_token, _ = _signup_and_auth(client, "other", "other@example.com")

    owner_board_response = client.post(
        "/api/boards",
        json={"title": "My Workshop", "hobby_type": "Woodworking", "is_public": True},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    owner_board_id = owner_board_response.get_json()["board"]["id"]

    other_board_response = client.post(
        "/api/boards",
        json={"title": "Community Craft Corner", "hobby_type": "Crafts", "is_public": True},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    other_board_id = other_board_response.get_json()["board"]["id"]

    client.post(
        f"/api/boards/{owner_board_id}/follow",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    empty_response = client.get(
        "/api/discover/boards",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert empty_response.status_code == 200
    assert empty_response.get_json()["boards"] == []

    discover_response = client.get(
        "/api/discover/boards?q=craft",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )

    assert discover_response.status_code == 200
    boards = discover_response.get_json()["boards"]
    assert len(boards) == 1
    assert boards[0]["id"] == other_board_id
    assert boards[0]["title"] == "Community Craft Corner"
