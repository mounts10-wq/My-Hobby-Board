import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

DEFAULT_DB_PATH = INSTANCE_DIR / "myhobbyboard.db"


def get_database_uri():
    configured_uri = os.getenv("DATABASE_URL")
    if not configured_uri:
        return f"sqlite:///{DEFAULT_DB_PATH}"

    # Handle Postgres URL scheme fix commonly provided by Render/Neon/Heroku
    if configured_uri.startswith("postgres://"):
        configured_uri = configured_uri.replace("postgres://", "postgresql://", 1)

    if configured_uri.startswith("postgresql://"):
        # Neon requires SSL; enforce it even if the copied connection string omits it.
        parsed = urlparse(configured_uri)
        query = parse_qs(parsed.query)
        if "sslmode" not in query:
            query["sslmode"] = ["require"]
            configured_uri = urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

    if configured_uri.startswith("sqlite:///") and not configured_uri.startswith("sqlite:////"):
        rel_str = configured_uri[len("sqlite:///"):]
        if not rel_str.startswith("/"):
            return f"sqlite:///{INSTANCE_DIR / Path(rel_str).name}"

    return configured_uri


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me-32chars")
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-change-me-32chars")
    # No refresh-token flow yet, so keep sessions long-lived to avoid users
    # getting silently logged out mid-session on a public-facing hobby app.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)