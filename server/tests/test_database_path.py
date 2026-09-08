import os
from pathlib import Path

from app import create_app


def test_database_uri_uses_instance_directory():
    app = create_app()
    expected_db = Path(__file__).resolve().parents[1] / "instance" / "myhobbyboard.db"

    assert app.config["SQLALCHEMY_DATABASE_URI"] == f"sqlite:///{expected_db}"


def test_relative_database_url_uses_instance_directory(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///myhobbyboard.db")

    app = create_app()
    expected_db = Path(__file__).resolve().parents[1] / "instance" / "myhobbyboard.db"

    assert app.config["SQLALCHEMY_DATABASE_URI"] == f"sqlite:///{expected_db}"
