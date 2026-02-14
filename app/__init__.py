import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

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

    return app
