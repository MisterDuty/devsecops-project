import html
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()
db = SQLAlchemy()

ALLOWED_STATUS = {"todo", "in_progress", "done"}
ALLOWED_PRIORITY = {"low", "medium", "high"}


def utc_now():
    return datetime.now(timezone.utc)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="todo")
    priority = db.Column(db.String(20), nullable=False, default="medium")
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


def sanitize(value):
    return html.escape(value.strip(), quote=True)


def validate_task(payload, partial=False):
    if not isinstance(payload, dict):
        return {}, {"payload": "JSON object expected"}

    errors = {}
    data = {}

    title = payload.get("title")
    if title is None and not partial:
        errors["title"] = "title is required"
    elif title is not None:
        if not isinstance(title, str) or not title.strip():
            errors["title"] = "title must be a non-empty string"
        elif len(title.strip()) > 120:
            errors["title"] = "title must be 120 characters or fewer"
        else:
            data["title"] = sanitize(title)

    description = payload.get("description")
    if description is not None:
        if not isinstance(description, str):
            errors["description"] = "description must be a string"
        elif len(description.strip()) > 500:
            errors["description"] = "description must be 500 characters or fewer"
        else:
            data["description"] = sanitize(description)

    status = payload.get("status")
    if status is not None:
        if status not in ALLOWED_STATUS:
            errors["status"] = f"status must be one of {sorted(ALLOWED_STATUS)}"
        else:
            data["status"] = status

    priority = payload.get("priority")
    if priority is not None:
        if priority not in ALLOWED_PRIORITY:
            errors["priority"] = f"priority must be one of {sorted(ALLOWED_PRIORITY)}"
        else:
            data["priority"] = priority

    return data, errors


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///tasks.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        FORCE_HTTPS=os.getenv("FORCE_HTTPS", "false").lower() == "true",
        RATELIMIT_DEFAULT=os.getenv("RATELIMIT_DEFAULT", "100 per hour"),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    Talisman(app, force_https=app.config["FORCE_HTTPS"])
    Limiter(
        get_remote_address,
        app=app,
        default_limits=[app.config["RATELIMIT_DEFAULT"]],
        storage_uri="memory://",
    )

    register_routes(app)
    with app.app_context():
        db.create_all()
    return app


def register_routes(app):
    @app.get("/")
    def index():
        return jsonify({"name": "devsecops-task-api", "status": "running"})

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/tasks")
    def list_tasks():
        tasks = Task.query.order_by(Task.created_at.desc()).all()
        return jsonify({"items": [task.to_dict() for task in tasks]})

    @app.post("/api/tasks")
    def create_task():
        data, errors = validate_task(request.get_json(silent=True) or {})
        if errors:
            return jsonify({"errors": errors}), 400

        task = Task(**data)
        db.session.add(task)
        return save_or_error(task, "task could not be created", 201)

    @app.get("/api/tasks/<int:task_id>")
    def get_task(task_id):
        return jsonify(Task.query.get_or_404(task_id).to_dict())

    @app.put("/api/tasks/<int:task_id>")
    def update_task(task_id):
        task = Task.query.get_or_404(task_id)
        data, errors = validate_task(request.get_json(silent=True) or {}, partial=True)
        if errors:
            return jsonify({"errors": errors}), 400

        for field, value in data.items():
            setattr(task, field, value)
        return save_or_error(task, "task could not be updated")

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id):
        task = Task.query.get_or_404(task_id)
        db.session.delete(task)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({"error": "task could not be deleted"}), 500
        return "", 204

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "resource not found"}), 404


def save_or_error(task, message, status_code=200):
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": message}), 500
    return jsonify(task.to_dict()), status_code


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
