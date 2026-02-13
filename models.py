from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rankings = db.relationship("ArtistRanking", backref="user", lazy="dynamic", order_by="ArtistRanking.rank_position")

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
