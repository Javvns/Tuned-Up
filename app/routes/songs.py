from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import SongRanking

bp = Blueprint("songs", __name__)


@bp.route("/", methods=["GET"])
@login_required
def list_rankings():
    rankings = SongRanking.query.filter_by(user_id=current_user.id).order_by(SongRanking.rank_position).all()
    return jsonify([{"id": r.id, "song_name": r.song_name, "rank_position": r.rank_position} for r in rankings])


@bp.route("/", methods=["POST"])
@login_required
def add_song():
    data = request.get_json() or {}
    name = (data.get("song_name") or "").strip()
    if not name:
        return jsonify({"error": "Song name is required"}), 400
    existing = SongRanking.query.filter_by(user_id=current_user.id, song_name=name).first()
    if existing:
        return jsonify({"error": "Song already in your list"}), 400
    max_pos = db.session.query(db.func.max(SongRanking.rank_position)).filter_by(user_id=current_user.id).scalar() or 0
    ranking = SongRanking(user_id=current_user.id, song_name=name, rank_position=max_pos + 1)
    db.session.add(ranking)
    db.session.commit()
    return jsonify({"id": ranking.id, "song_name": ranking.song_name, "rank_position": ranking.rank_position}), 201


@bp.route("/reorder", methods=["PUT"])
@login_required
def reorder():
    data = request.get_json() or {}
    order = data.get("order")
    if not order or not isinstance(order, list):
        return jsonify({"error": "Order list is required"}), 400
    rankings = {r.id: r for r in SongRanking.query.filter_by(user_id=current_user.id).all()}
    for position, id_ in enumerate(order, start=1):
        if id_ in rankings:
            rankings[id_].rank_position = position
    db.session.commit()
    return jsonify({"ok": True})


@bp.route("/<int:song_id>", methods=["DELETE"])
@login_required
def remove_song(song_id):
    ranking = SongRanking.query.filter_by(id=song_id, user_id=current_user.id).first()
    if not ranking:
        return jsonify({"error": "Not found"}), 404
    old_pos = ranking.rank_position
    db.session.delete(ranking)
    for r in SongRanking.query.filter_by(user_id=current_user.id).filter(SongRanking.rank_position > old_pos).all():
        r.rank_position -= 1
    db.session.commit()
    return jsonify({"ok": True}), 200
