from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import AlbumRanking

bp = Blueprint("albums", __name__)


@bp.route("/", methods=["GET"])
@login_required
def list_rankings():
    rankings = AlbumRanking.query.filter_by(user_id=current_user.id).order_by(AlbumRanking.rank_position).all()
    return jsonify([{"id": r.id, "album_name": r.album_name, "rank_position": r.rank_position} for r in rankings])


@bp.route("/", methods=["POST"])
@login_required
def add_album():
    data = request.get_json() or {}
    name = (data.get("album_name") or "").strip()
    if not name:
        return jsonify({"error": "Album name is required"}), 400
    existing = AlbumRanking.query.filter_by(user_id=current_user.id, album_name=name).first()
    if existing:
        return jsonify({"error": "Album already in your list"}), 400
    max_pos = db.session.query(db.func.max(AlbumRanking.rank_position)).filter_by(user_id=current_user.id).scalar() or 0
    ranking = AlbumRanking(user_id=current_user.id, album_name=name, rank_position=max_pos + 1)
    db.session.add(ranking)
    db.session.commit()
    return jsonify({"id": ranking.id, "album_name": ranking.album_name, "rank_position": ranking.rank_position}), 201


@bp.route("/reorder", methods=["PUT"])
@login_required
def reorder():
    data = request.get_json() or {}
    order = data.get("order")
    if not order or not isinstance(order, list):
        return jsonify({"error": "Order list is required"}), 400
    rankings = {r.id: r for r in AlbumRanking.query.filter_by(user_id=current_user.id).all()}
    for position, id_ in enumerate(order, start=1):
        if id_ in rankings:
            rankings[id_].rank_position = position
    db.session.commit()
    return jsonify({"ok": True})


@bp.route("/<int:album_id>", methods=["DELETE"])
@login_required
def remove_album(album_id):
    ranking = AlbumRanking.query.filter_by(id=album_id, user_id=current_user.id).first()
    if not ranking:
        return jsonify({"error": "Not found"}), 404
    old_pos = ranking.rank_position
    db.session.delete(ranking)
    for r in AlbumRanking.query.filter_by(user_id=current_user.id).filter(AlbumRanking.rank_position > old_pos).all():
        r.rank_position -= 1
    db.session.commit()
    return jsonify({"ok": True}), 200
