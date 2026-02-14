import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Load .env from project root (parent of app/) and from cwd
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)
load_dotenv()  # fallback: .env in current working directory

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "tuned-up-dev-secret-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tunedup.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes import main, auth, artists, albums, songs, spotify_api
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp, url_prefix="/auth")
    app.register_blueprint(artists.bp, url_prefix="/api/artists")
    app.register_blueprint(albums.bp, url_prefix="/api/albums")
    app.register_blueprint(songs.bp, url_prefix="/api/songs")
    app.register_blueprint(spotify_api.bp, url_prefix="/api/spotify")

    with app.app_context():
        db.create_all()
        _add_spotify_columns_if_missing(app)

    return app


def _add_spotify_columns_if_missing(app):
    """Add spotify_id and spotify_refresh_token to users table if they don't exist."""
    from sqlalchemy import text
    try:
        result = db.session.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]
    except Exception:
        return
    if "spotify_id" not in columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN spotify_id VARCHAR(80)"))
    if "spotify_refresh_token" not in columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN spotify_refresh_token VARCHAR(256)"))
    if "spotify_access_token" not in columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN spotify_access_token TEXT"))
    if "spotify_token_expires_at" not in columns:
        db.session.execute(text("ALTER TABLE users ADD COLUMN spotify_token_expires_at BIGINT"))
    db.session.commit()
