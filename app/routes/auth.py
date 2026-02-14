from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.models import User
from app.spotify_client import get_spotify_oauth, spotify_configured

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        if not username or not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("register.html")
        if User.query.filter_by(username=username).first():
            flash("That username is already taken.", "error")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("That email is already registered.", "error")
            return render_template("register.html")
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome to Tuned Up!", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Welcome back!", "success")
            next_url = request.args.get("next") or url_for("main.dashboard")
            return redirect(next_url)
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    logout_user()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("main.index"))


@bp.route("/spotify")
def spotify_login():
    if not current_user.is_authenticated:
        flash("Please log in first.", "error")
        return redirect(url_for("auth.login"))
    if not spotify_configured():
        flash("Spotify is not configured.", "error")
        return redirect(url_for("main.dashboard"))
    auth = get_spotify_oauth()
    state = str(current_user.id)
    url = auth.get_authorize_url(state=state)
    return redirect(url)


@bp.route("/spotify/callback")
def spotify_callback():
    if not current_user.is_authenticated:
        flash("Please log in first.", "error")
        return redirect(url_for("auth.login"))
    if not spotify_configured():
        flash("Spotify is not configured.", "error")
        return redirect(url_for("main.dashboard"))
    code = request.args.get("code")
    state = request.args.get("state")
    if not code or state != str(current_user.id):
        flash("Spotify connection was cancelled or invalid.", "error")
        return redirect(url_for("main.dashboard"))
    auth = get_spotify_oauth()
    try:
        token_info = auth.get_access_token(code, as_dict=True, check_cache=False)
    except Exception:
        flash("Could not connect to Spotify.", "error")
        return redirect(url_for("main.dashboard"))
    if token_info:
        current_user.spotify_refresh_token = token_info.get("refresh_token")
        current_user.spotify_id = token_info.get("user_id")
        current_user.spotify_access_token = token_info.get("access_token")
        current_user.spotify_token_expires_at = token_info.get("expires_at")
        db.session.commit()
        flash("Spotify connected. You can get personalized recommendations.", "success")
    else:
        flash("Could not get Spotify token.", "error")
    return redirect(url_for("main.dashboard"))
