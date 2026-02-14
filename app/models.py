from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rankings = db.relationship(
        "ArtistRanking", backref="user", lazy="dynamic", order_by="ArtistRanking.rank_position"
    )
    album_rankings = db.relationship(
        "AlbumRanking", backref="user", lazy="dynamic", order_by="AlbumRanking.rank_position"
    )
    song_rankings = db.relationship(
        "SongRanking", backref="user", lazy="dynamic", order_by="SongRanking.rank_position"
    )
    spotify_id = db.Column(db.String(80), nullable=True)
    spotify_refresh_token = db.Column(db.String(256), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ArtistRanking(db.Model):
    __tablename__ = "artist_rankings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    artist_name = db.Column(db.String(200), nullable=False)
    rank_position = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "artist_name", name="uq_user_artist"),)


class AlbumRanking(db.Model):
    __tablename__ = "album_rankings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    album_name = db.Column(db.String(300), nullable=False)
    rank_position = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "album_name", name="uq_user_album"),)


class SongRanking(db.Model):
    __tablename__ = "song_rankings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    song_name = db.Column(db.String(300), nullable=False)
    rank_position = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "song_name", name="uq_user_song"),)
