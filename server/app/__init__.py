import os
from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour"])


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.route("/")
    def root():
        return redirect("/api/health")

    cors_origins = os.getenv("CORS_ORIGINS")
    if cors_origins:
        origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
        CORS(app, origins=origins, supports_credentials=True)
    else:
        CORS(app, supports_credentials=True)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    from . import models
    from .routes import api

    # Schema is managed by Flask-Migrate (see `flask db upgrade`), not auto-created here.

    app.register_blueprint(api, url_prefix="/api")

    return app