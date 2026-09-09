import json
import os
import re
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    decode_token,
)

from . import db
from .models import User, Board, Task, BoardUpdate, UserFollow, BoardUpdateComment, BoardFollow

api = Blueprint("api", __name__)

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "instance" / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_TASK_STATUSES = {"Not Started", "In Progress", "Complete"}
ALLOWED_TASK_PRIORITIES = {"Low", "Medium", "High"}


def can_view_board(board, viewer_user_id):
    return board.user_id == viewer_user_id or bool(board.is_public)


def upload_media_file(media_file):
    """Store an uploaded file and return its public media_url.

    Uses Cloudinary when configured (persists across deploys); otherwise
    falls back to local disk, which is fine for local development but is
    wiped on every deploy/restart on most hosting platforms.
    """
    if os.getenv("CLOUDINARY_URL"):
        import cloudinary.uploader

        result = cloudinary.uploader.upload(media_file, resource_type="auto", folder="myhobbyboard")
        return result["secure_url"]

    filename = secure_filename(media_file.filename)
    if not filename:
        return None

    saved_path = UPLOAD_DIR / filename
    counter = 1
    while saved_path.exists():
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        saved_path = UPLOAD_DIR / f"{stem}-{counter}{suffix}"
        counter += 1

    media_file.save(saved_path)
    return f"/api/uploads/{saved_path.name}"


def build_local_plan_suggestions(title, description, materials, notes):
    context = " ".join([title, description, materials, notes]).lower()
    title_label = title or "this project"
    suggestions = []

    if any(keyword in context for keyword in ["build", "make", "repair", "restore", "create", "assemble"]):
        suggestions.append(f"Break {title_label} into one small milestone you can finish this week.")
    elif any(keyword in context for keyword in ["learn", "study", "practice", "read", "research"]):
        suggestions.append(f"Create a short study sequence for {title_label} so progress stays steady.")
    else:
        suggestions.append(f"Start with one concrete first step for {title_label}.")

    if materials:
        suggestions.append(f"Use your materials as a prep checklist: {materials}.")
    else:
        suggestions.append("Add a few materials so the assistant can suggest a better prep plan.")

    if notes:
        suggestions.append(f"Turn your note into a specific next action: {notes}")
    else:
        suggestions.append("Write one short note about your next step so the plan feels more real.")

    if any(keyword in context for keyword in ["week", "month", "timeline", "schedule", "deadline"]):
        suggestions.append("Set a simple checkpoint date to keep momentum going.")
    else:
        suggestions.append("Pick a target date so the plan feels easier to follow.")

    return suggestions[:4]


def parse_suggestions_from_ai_text(text):
    cleaned_text = (text or "").strip()
    if not cleaned_text:
        return []

    if cleaned_text.startswith("```"):
        fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned_text, re.DOTALL)
        if fence_match:
            cleaned_text = fence_match.group(1).strip()

    try:
        parsed = json.loads(cleaned_text)
        if isinstance(parsed, dict):
            parsed = parsed.get("suggestions", [])

        if isinstance(parsed, list):
            suggestions = []
            for item in parsed:
                if isinstance(item, str) and item.strip():
                    suggestions.append(item.strip())
                elif isinstance(item, dict):
                    candidate = str(item.get("suggestion") or item.get("text") or "").strip()
                    if candidate:
                        suggestions.append(candidate)
            if suggestions:
                return suggestions[:4]
    except Exception:
        pass

    quoted_values = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', cleaned_text)
    if quoted_values:
        suggestions = [item.strip() for item in quoted_values if item.strip()]
        return suggestions[:4]

    line_items = [
        re.sub(r"^[-*\d.)\s]+", "", line).strip()
        for line in cleaned_text.splitlines()
        if line.strip()
    ]
    return line_items[:4]


def normalize_plan_suggestions(raw_suggestions):
    normalized = []

    for item in raw_suggestions or []:
        suggestion = re.sub(r"\s+", " ", str(item).strip())
        suggestion = re.sub(r"^[-*\d.)\s]+", "", suggestion).strip()
        if not suggestion:
            continue

        if suggestion[-1] not in {".", "!", "?"}:
            suggestion = f"{suggestion}."

        normalized.append(suggestion)

    return normalized[:4]


def build_assistant_fallback_response(title, description, materials, notes):
    suggestions = normalize_plan_suggestions(
        build_local_plan_suggestions(title, description, materials, notes)
    )
    return jsonify({"suggestions": suggestions, "source": "fallback"}), 200


@api.route("/health", methods=["GET"])
def health_check():
    return jsonify({"message": "MyHobbyBoard API is running"}), 200


@api.route("/uploads/<path:filename>", methods=["GET"])
def serve_upload(filename):
    token = request.args.get("token", "").strip()
    if not token:
        return jsonify({"error": "Access denied"}), 403

    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        return jsonify({"error": "Access denied"}), 403

    upload_path = UPLOAD_DIR / filename
    if not upload_path.exists() or not upload_path.is_file():
        return jsonify({"error": "Upload not found"}), 404

    update = BoardUpdate.query.filter_by(media_url=f"/api/uploads/{filename}").first()
    if not update:
        return jsonify({"error": "Upload not found"}), 404

    board = update.board
    if not board or not can_view_board(board, user_id):
        return jsonify({"error": "Access denied"}), 403

    if board.user_id != user_id:
        follow_exists = BoardFollow.query.filter_by(
            follower_user_id=user_id,
            board_id=board.id,
        ).first()
        if not follow_exists:
            return jsonify({"error": "Access denied"}), 403

    return send_from_directory(UPLOAD_DIR, filename)


@api.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}

    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    existing_username = User.query.filter_by(username=username).first()
    if existing_username:
        return jsonify({"error": "Username is already taken"}), 409

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({"error": "Email is already registered"}), 409

    user = User(username=username, email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "User created successfully",
        "user": user.to_dict(),
        "access_token": access_token
    }), 201


@api.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
        "access_token": access_token
    }), 200


@api.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user.to_dict()}), 200


@api.route("/logout", methods=["POST"])
def logout():
    return jsonify({
        "message": "Logout successful. Remove the token on the frontend."
    }), 200


@api.route("/dashboard/stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    user_id = int(get_jwt_identity())

    board_count = Board.query.filter_by(user_id=user_id).count()

    user_tasks = Task.query.join(Board).filter(Board.user_id == user_id)
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(Task.status == "Complete").count()
    in_progress_tasks = user_tasks.filter(Task.status == "In Progress").count()
    not_started_tasks = user_tasks.filter(Task.status == "Not Started").count()
    high_priority_tasks = user_tasks.filter(Task.priority == "High").count()

    completion_rate = round((completed_tasks / total_tasks) * 100, 1) if total_tasks else 0

    return jsonify({
        "stats": {
            "board_count": board_count,
            "task_count": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "not_started_tasks": not_started_tasks,
            "high_priority_tasks": high_priority_tasks,
            "completion_rate": completion_rate
        }
    }), 200


@api.route("/boards", methods=["GET"])
@jwt_required()
def get_boards():
    user_id = int(get_jwt_identity())

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    paginated_boards = Board.query.filter_by(user_id=user_id) \
        .order_by(Board.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    boards = [board.to_dict() for board in paginated_boards.items]

    return jsonify({
        "boards": boards,
        "page": paginated_boards.page,
        "per_page": paginated_boards.per_page,
        "total": paginated_boards.total,
        "pages": paginated_boards.pages
    }), 200


@api.route("/boards", methods=["POST"])
@jwt_required()
def create_board():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    title = str(data.get("title", "")).strip()
    hobby_type = str(data.get("hobby_type", "")).strip()
    description = str(data.get("description", "")).strip()
    materials = str(data.get("materials", "")).strip()
    notes = str(data.get("notes", "")).strip()
    is_public = bool(data.get("is_public", False))

    if not title or not hobby_type:
        return jsonify({"error": "Title and hobby type are required"}), 400

    board = Board(
        title=title,
        hobby_type=hobby_type,
        description=description,
        materials=materials,
        notes=notes,
        is_public=is_public,
        user_id=user_id
    )

    db.session.add(board)
    db.session.commit()

    return jsonify({
        "message": "Board created successfully",
        "board": board.to_dict()
    }), 201


@api.route("/boards/<int:board_id>", methods=["GET"])
@jwt_required()
def get_board(board_id):
    user_id = int(get_jwt_identity())

    board = db.session.get(Board, board_id)

    if not board or not can_view_board(board, user_id):
        return jsonify({"error": "Board not found"}), 404

    board_data = board.to_dict(include_tasks=True)
    board_data["is_owner"] = board.user_id == user_id
    board_data["owner_username"] = board.user.username if board.user else None

    return jsonify({"board": board_data}), 200


@api.route("/boards/<int:board_id>", methods=["PATCH"])
@jwt_required()
def update_board(board_id):
    user_id = int(get_jwt_identity())

    board = Board.query.filter_by(id=board_id, user_id=user_id).first()

    if not board:
        return jsonify({"error": "Board not found"}), 404

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = data.get("title", "").strip()
        if not title:
            return jsonify({"error": "Title cannot be empty"}), 400
        board.title = title

    if "hobby_type" in data:
        hobby_type = data.get("hobby_type", "").strip()
        if not hobby_type:
            return jsonify({"error": "Hobby type cannot be empty"}), 400
        board.hobby_type = hobby_type

    if "description" in data:
        board.description = data.get("description", "").strip()

    if "materials" in data:
        board.materials = data.get("materials", "").strip()

    if "notes" in data:
        board.notes = data.get("notes", "").strip()

    if "is_public" in data:
        board.is_public = bool(data.get("is_public"))

    db.session.commit()

    return jsonify({
        "message": "Board updated successfully",
        "board": board.to_dict()
    }), 200


@api.route("/boards/<int:board_id>", methods=["DELETE"])
@jwt_required()
def delete_board(board_id):
    user_id = int(get_jwt_identity())

    board = Board.query.filter_by(id=board_id, user_id=user_id).first()

    if not board:
        return jsonify({"error": "Board not found"}), 404

    db.session.delete(board)
    db.session.commit()

    return jsonify({"message": "Board deleted successfully"}), 200


@api.route("/assistant/plan", methods=["POST"])
def generate_plan_suggestions():
    data = request.get_json() or {}
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    materials = str(data.get("materials", "")).strip()
    notes = str(data.get("notes", "")).strip()

    prompt = f"You are a hobby project planning assistant. Create 4 helpful suggestions for a project called '{title or 'a new hobby project'}'."

    if description:
        prompt += f" The project description is: {description}."
    if materials:
        prompt += f" The materials mentioned are: {materials}."
    if notes:
        prompt += f" The planning notes are: {notes}."

    prompt += (
        " Return exactly 4 concise suggestions as a JSON array of strings."
        " Each suggestion should start with an action verb and include a concrete outcome"
        " or a near-term timeframe. Keep each suggestion under 20 words."
        " Do not return markdown or additional commentary."
    )

    # Keep automated tests stable and independent of external AI services.
    if current_app.config.get("TESTING") and os.getenv("ENABLE_AI_IN_TESTS", "").lower() not in {"1", "true", "yes", "on"}:
        return build_assistant_fallback_response(title, description, materials, notes)

    gemini_key = os.getenv("GEMINI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    # 1. Try Google Gemini if configured
    if gemini_key:
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip() or "gemini-3.6-flash"
        try:
            import requests

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    # Reasoning models spend part of this budget "thinking" before answering.
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2048,
                    },
                },
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            candidates = payload.get("candidates", [])
            text = ""
            if candidates and isinstance(candidates, list):
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and isinstance(parts, list):
                    text = parts[0].get("text", "")

            if text:
                suggestions = normalize_plan_suggestions(parse_suggestions_from_ai_text(text))
                # Reject truncated responses (e.g. reasoning models cut off before finishing).
                if len(suggestions) >= 3:
                    return jsonify({"suggestions": suggestions[:4], "source": "gemini"}), 200
            current_app.logger.warning("Gemini returned no usable text: %s", payload)
        except Exception as exc:
            current_app.logger.exception("Gemini assistant call failed: %s", exc)

    # 2. Try Anthropic if configured
    if anthropic_key:
        anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5").strip() or "claude-sonnet-5"
        try:
            import requests

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": anthropic_model,
                    "max_tokens": 400,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            content = payload.get("content", [])
            text = ""
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text += item.get("text", "")

            if text:
                suggestions = normalize_plan_suggestions(parse_suggestions_from_ai_text(text))
                if len(suggestions) >= 3:
                    return jsonify({"suggestions": suggestions[:4], "source": "anthropic"}), 200
        except Exception as exc:
            current_app.logger.exception("Anthropic assistant call failed: %s", exc)

    # 3. Fallback to smart local suggestions if no AI key or AI request fails
    return build_assistant_fallback_response(title, description, materials, notes)


@api.route("/boards/<int:board_id>/updates", methods=["GET"])
@jwt_required()
def get_board_updates(board_id):
    user_id = int(get_jwt_identity())

    board = db.session.get(Board, board_id)

    if not board or not can_view_board(board, user_id):
        return jsonify({"error": "Board not found"}), 404

    updates = BoardUpdate.query.filter_by(board_id=board.id) \
        .order_by(BoardUpdate.created_at.desc()) \
        .all()

    return jsonify({"updates": [update.to_dict() for update in updates]}), 200


@api.route("/me/following", methods=["GET"])
@jwt_required()
def get_following_users():
    user_id = int(get_jwt_identity())

    follow_rows = UserFollow.query.filter_by(follower_user_id=user_id).all()
    following_ids = [row.followed_user_id for row in follow_rows]

    return jsonify({"following_user_ids": following_ids}), 200


@api.route("/boards/<int:board_id>/updates", methods=["POST"])
@jwt_required()
def create_board_update(board_id):
    user_id = int(get_jwt_identity())

    board = Board.query.filter_by(id=board_id, user_id=user_id).first()

    if not board:
        return jsonify({"error": "Board not found"}), 404

    if request.content_type and "multipart/form-data" in request.content_type:
        content = str(request.form.get("content", "")).strip()
        media_url = str(request.form.get("media_url", "")).strip()
        media_file = request.files.get("media_file")
    else:
        data = request.get_json(silent=True) or {}
        content = str(data.get("content", "")).strip()
        media_url = str(data.get("media_url", "")).strip()
        media_file = None

    if not content:
        return jsonify({"error": "Update content is required"}), 400

    resolved_media_url = media_url or None
    if media_file and media_file.filename:
        try:
            resolved_media_url = upload_media_file(media_file)
        except Exception as exc:
            current_app.logger.exception("Media upload failed: %s", exc)
            return jsonify({"error": "Media upload failed. Please try again."}), 502

        if not resolved_media_url:
            return jsonify({"error": "Invalid file name"}), 400

    update = BoardUpdate(
        content=content,
        media_url=resolved_media_url,
        board_id=board.id,
        user_id=user_id
    )

    db.session.add(update)
    db.session.commit()

    return jsonify({
        "message": "Update created successfully",
        "update": update.to_dict()
    }), 201


@api.route("/updates/<int:update_id>", methods=["DELETE"])
@jwt_required()
def delete_board_update(update_id):
    user_id = int(get_jwt_identity())

    update = BoardUpdate.query.join(Board).filter(
        BoardUpdate.id == update_id,
        Board.user_id == user_id
    ).first()

    if not update:
        return jsonify({"error": "Update not found"}), 404

    db.session.delete(update)
    db.session.commit()

    return jsonify({"message": "Update deleted successfully"}), 200


@api.route("/users/<int:target_user_id>/follow", methods=["POST"])
@jwt_required()
def follow_user(target_user_id):
    user_id = int(get_jwt_identity())

    if user_id == target_user_id:
        return jsonify({"error": "You cannot follow yourself"}), 400

    target_user = db.session.get(User, target_user_id)
    if not target_user:
        return jsonify({"error": "User not found"}), 404

    existing = UserFollow.query.filter_by(
        follower_user_id=user_id,
        followed_user_id=target_user_id
    ).first()
    if existing:
        return jsonify({"error": "You are already following this user"}), 409

    follow = UserFollow(follower_user_id=user_id, followed_user_id=target_user_id)
    db.session.add(follow)
    db.session.commit()

    return jsonify({"message": "Now following user"}), 201


@api.route("/users/<int:target_user_id>/follow", methods=["DELETE"])
@jwt_required()
def unfollow_user(target_user_id):
    user_id = int(get_jwt_identity())

    follow = UserFollow.query.filter_by(
        follower_user_id=user_id,
        followed_user_id=target_user_id
    ).first()
    if not follow:
        return jsonify({"error": "Follow relationship not found"}), 404

    db.session.delete(follow)
    db.session.commit()

    return jsonify({"message": "Unfollowed user"}), 200


@api.route("/feed", methods=["GET"])
@jwt_required()
def get_social_feed():
    user_id = int(get_jwt_identity())

    followed_board_ids = db.session.query(BoardFollow.board_id).filter_by(
        follower_user_id=user_id
    )

    updates = BoardUpdate.query.join(Board).filter(
        (Board.user_id == user_id)
        | ((Board.id.in_(followed_board_ids)) & (Board.is_public.is_(True)))
    ).order_by(BoardUpdate.created_at.desc()).limit(50).all()

    payload = []
    for update in updates:
        update_data = update.to_dict()
        update_data["board_title"] = update.board.title if update.board else None
        update_data["hobby_type"] = update.board.hobby_type if update.board else None
        payload.append(update_data)

    return jsonify({"updates": payload}), 200


@api.route("/me/following/boards", methods=["GET"])
@jwt_required()
def get_following_boards():
    user_id = int(get_jwt_identity())

    followed_board_ids = db.session.query(BoardFollow.board_id).filter_by(
        follower_user_id=user_id
    )

    boards = Board.query.filter(
        Board.id.in_(followed_board_ids),
        Board.is_public.is_(True)
    ).order_by(Board.created_at.desc()).limit(100).all()

    payload = []
    for board in boards:
        board_data = board.to_dict()
        board_data["owner_username"] = board.user.username if board.user else None
        payload.append(board_data)

    return jsonify({"boards": payload}), 200


@api.route("/boards/<int:board_id>/follow", methods=["POST"])
@jwt_required()
def follow_board(board_id):
    user_id = int(get_jwt_identity())

    board = db.session.get(Board, board_id)
    if not board or not board.is_public:
        return jsonify({"error": "Board not found"}), 404

    if board.user_id == user_id:
        return jsonify({"error": "You cannot follow your own board"}), 400

    existing = BoardFollow.query.filter_by(
        follower_user_id=user_id,
        board_id=board_id
    ).first()
    if existing:
        return jsonify({"error": "You are already following this board"}), 409

    follow = BoardFollow(follower_user_id=user_id, board_id=board_id)
    db.session.add(follow)
    db.session.commit()

    return jsonify({"message": "Now following board"}), 201


@api.route("/boards/<int:board_id>/follow", methods=["DELETE"])
@jwt_required()
def unfollow_board(board_id):
    user_id = int(get_jwt_identity())

    follow = BoardFollow.query.filter_by(
        follower_user_id=user_id,
        board_id=board_id
    ).first()
    if not follow:
        return jsonify({"error": "Board follow relationship not found"}), 404

    db.session.delete(follow)
    db.session.commit()

    return jsonify({"message": "Unfollowed board"}), 200


@api.route("/discover/boards", methods=["GET"])
@jwt_required()
def discover_boards():
    user_id = int(get_jwt_identity())
    query_text = str(request.args.get("q", "")).strip()
    hobby_filter = str(request.args.get("hobby", "")).strip()

    if not query_text and not hobby_filter:
        return jsonify({"boards": []}), 200

    query = Board.query.filter_by(is_public=True).filter(Board.user_id != user_id)

    followed_board_ids = [
        row.board_id for row in BoardFollow.query.filter_by(follower_user_id=user_id).all()
    ]
    if followed_board_ids:
        query = query.filter(Board.id.notin_(followed_board_ids))

    if query_text:
        pattern = f"%{query_text}%"
        query = query.filter(
            (Board.title.ilike(pattern))
            | (Board.description.ilike(pattern))
            | (Board.notes.ilike(pattern))
        )

    if hobby_filter:
        hobby_pattern = f"%{hobby_filter}%"
        query = query.filter(Board.hobby_type.ilike(hobby_pattern))

    boards = query.order_by(Board.created_at.desc()).limit(50).all()

    payload = []
    for board in boards:
        board_data = board.to_dict()
        board_data["owner_username"] = board.user.username if board.user else None
        payload.append(board_data)

    return jsonify({"boards": payload}), 200


@api.route("/updates/<int:update_id>/comments", methods=["GET"])
@jwt_required()
def get_update_comments(update_id):
    user_id = int(get_jwt_identity())

    update = db.session.get(BoardUpdate, update_id)
    if not update:
        return jsonify({"error": "Update not found"}), 404

    if not can_view_board(update.board, user_id):
        return jsonify({"error": "Update not found"}), 404

    comments = BoardUpdateComment.query.filter_by(update_id=update_id) \
        .order_by(BoardUpdateComment.created_at.asc()) \
        .all()

    return jsonify({"comments": [comment.to_dict() for comment in comments]}), 200


@api.route("/updates/<int:update_id>/comments", methods=["POST"])
@jwt_required()
def create_update_comment(update_id):
    user_id = int(get_jwt_identity())

    update = db.session.get(BoardUpdate, update_id)
    if not update:
        return jsonify({"error": "Update not found"}), 404

    if not can_view_board(update.board, user_id):
        return jsonify({"error": "Update not found"}), 404

    data = request.get_json(silent=True) or {}
    content = str(data.get("content", "")).strip()

    if not content:
        return jsonify({"error": "Comment content is required"}), 400

    comment = BoardUpdateComment(content=content, update_id=update_id, user_id=user_id)
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "message": "Comment created successfully",
        "comment": comment.to_dict()
    }), 201

@api.route("/boards/<int:board_id>/tasks", methods=["GET"])
@jwt_required()
def get_tasks_for_board(board_id):
    user_id = int(get_jwt_identity())

    board = db.session.get(Board, board_id)

    if not board or not can_view_board(board, user_id):
        return jsonify({"error": "Board not found"}), 404

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    paginated_tasks = Task.query.filter_by(board_id=board.id) \
        .order_by(Task.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    tasks = [task.to_dict() for task in paginated_tasks.items]

    return jsonify({
        "tasks": tasks,
        "page": paginated_tasks.page,
        "per_page": paginated_tasks.per_page,
        "total": paginated_tasks.total,
        "pages": paginated_tasks.pages
    }), 200


@api.route("/boards/<int:board_id>/tasks", methods=["POST"])
@jwt_required()
def create_task(board_id):
    user_id = int(get_jwt_identity())

    board = Board.query.filter_by(id=board_id, user_id=user_id).first()

    if not board:
        return jsonify({"error": "Board not found"}), 404

    data = request.get_json(silent=True) or {}

    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    status = str(data.get("status", "Not Started")).strip()
    priority = str(data.get("priority", "Medium")).strip()

    if not title:
        return jsonify({"error": "Task title is required"}), 400

    if status not in ALLOWED_TASK_STATUSES:
        return jsonify({
            "error": "Invalid task status",
            "allowed_values": sorted(ALLOWED_TASK_STATUSES)
        }), 400

    if priority not in ALLOWED_TASK_PRIORITIES:
        return jsonify({
            "error": "Invalid task priority",
            "allowed_values": sorted(ALLOWED_TASK_PRIORITIES)
        }), 400

    task = Task(
        title=title,
        description=description,
        status=status,
        priority=priority,
        board_id=board.id
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({
        "message": "Task created successfully",
        "task": task.to_dict()
    }), 201


@api.route("/tasks/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    user_id = int(get_jwt_identity())

    task = Task.query.join(Board).filter(
        Task.id == task_id,
        Board.user_id == user_id
    ).first()

    if not task:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"task": task.to_dict()}), 200


@api.route("/tasks/<int:task_id>", methods=["PATCH"])
@jwt_required()
def update_task(task_id):
    user_id = int(get_jwt_identity())

    task = Task.query.join(Board).filter(
        Task.id == task_id,
        Board.user_id == user_id
    ).first()

    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = str(data.get("title", "")).strip()
        if not title:
            return jsonify({"error": "Task title cannot be empty"}), 400
        task.title = title

    if "description" in data:
        task.description = str(data.get("description", "")).strip()

    if "status" in data:
        status = str(data.get("status", "")).strip()
        if status not in ALLOWED_TASK_STATUSES:
            return jsonify({
                "error": "Invalid task status",
                "allowed_values": sorted(ALLOWED_TASK_STATUSES)
            }), 400
        task.status = status

    if "priority" in data:
        priority = str(data.get("priority", "")).strip()
        if priority not in ALLOWED_TASK_PRIORITIES:
            return jsonify({
                "error": "Invalid task priority",
                "allowed_values": sorted(ALLOWED_TASK_PRIORITIES)
            }), 400
        task.priority = priority

    db.session.commit()

    return jsonify({
        "message": "Task updated successfully",
        "task": task.to_dict()
    }), 200


@api.route("/tasks/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    user_id = int(get_jwt_identity())

    task = Task.query.join(Board).filter(
        Task.id == task_id,
        Board.user_id == user_id
    ).first()

    if not task:
        return jsonify({"error": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted successfully"}), 200
