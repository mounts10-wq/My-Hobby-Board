from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)

    boards = db.relationship(
        "Board",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    board_updates = db.relationship(
        "BoardUpdate",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    written_update_comments = db.relationship(
        "BoardUpdateComment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    following = db.relationship(
        "UserFollow",
        foreign_keys="UserFollow.follower_user_id",
        back_populates="follower",
        cascade="all, delete-orphan"
    )
    followers = db.relationship(
        "UserFollow",
        foreign_keys="UserFollow.followed_user_id",
        back_populates="followed",
        cascade="all, delete-orphan"
    )
    followed_boards = db.relationship(
        "BoardFollow",
        foreign_keys="BoardFollow.follower_user_id",
        back_populates="follower",
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email
        }


class Board(db.Model):
    __tablename__ = "boards"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    hobby_type = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=True)
    materials = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = db.relationship("User", back_populates="boards")
    tasks = db.relationship(
        "Task",
        back_populates="board",
        cascade="all, delete-orphan"
    )
    updates = db.relationship(
        "BoardUpdate",
        back_populates="board",
        cascade="all, delete-orphan"
    )
    followers = db.relationship(
        "BoardFollow",
        back_populates="board",
        cascade="all, delete-orphan"
    )

    def to_dict(self, include_tasks=False):
        board_dict = {
            "id": self.id,
            "title": self.title,
            "hobby_type": self.hobby_type,
            "description": self.description,
            "materials": self.materials,
            "notes": self.notes,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id
        }

        if include_tasks:
            board_dict["tasks"] = [task.to_dict() for task in self.tasks]

        return board_dict


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="Not Started")
    priority = db.Column(db.String(50), default="Medium")
    created_at = db.Column(db.DateTime, default=utcnow)

    board_id = db.Column(db.Integer, db.ForeignKey("boards.id"), nullable=False)

    board = db.relationship("Board", back_populates="tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "board_id": self.board_id
        }


class BoardUpdate(db.Model):
    __tablename__ = "board_updates"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    media_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    board_id = db.Column(db.Integer, db.ForeignKey("boards.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    board = db.relationship("Board", back_populates="updates")
    user = db.relationship("User", back_populates="board_updates")
    comments = db.relationship(
        "BoardUpdateComment",
        back_populates="update",
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "media_url": self.media_url,
            "created_at": self.created_at.isoformat(),
            "board_id": self.board_id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
        }


class UserFollow(db.Model):
    __tablename__ = "user_follows"

    id = db.Column(db.Integer, primary_key=True)
    follower_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    followed_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    follower = db.relationship("User", foreign_keys=[follower_user_id], back_populates="following")
    followed = db.relationship("User", foreign_keys=[followed_user_id], back_populates="followers")

    __table_args__ = (
        db.UniqueConstraint("follower_user_id", "followed_user_id", name="uq_user_follow_pair"),
    )


class BoardFollow(db.Model):
    __tablename__ = "board_follows"

    id = db.Column(db.Integer, primary_key=True)
    follower_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    board_id = db.Column(db.Integer, db.ForeignKey("boards.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    follower = db.relationship("User", back_populates="followed_boards")
    board = db.relationship("Board", back_populates="followers")

    __table_args__ = (
        db.UniqueConstraint("follower_user_id", "board_id", name="uq_board_follow_pair"),
    )


class BoardUpdateComment(db.Model):
    __tablename__ = "board_update_comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    update_id = db.Column(db.Integer, db.ForeignKey("board_updates.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    update = db.relationship("BoardUpdate", back_populates="comments")
    user = db.relationship("User", back_populates="written_update_comments")

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "update_id": self.update_id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
        }