"""
Spotify API routes: search suggestions (app token) and recommendations (user token).
"""
import threading
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.spotify_client import (
    get_app_spotify,
    get_spotify_for_user,
    spotify_configured,
)

bp = Blueprint("spotify_api", __name__)


@bp.route("/status")
@login_required
def status():
    """Return whether the current user has connected Spotify."""
    return jsonify({"connected": bool(current_user.spotify_refresh_token)})


@bp.route("/suggest")
def suggest():
    """
    Search Spotify for artists or tracks. Uses app credentials (no user login required).
    Query params: q (search string), type (artist, track, or both), limit (max 10).
    """
    if not spotify_configured():
        return jsonify({"error": "Spotify not configured"}), 503
    q = (request.args.get("q") or "").strip()
    if not q or len(q) < 2:
        return jsonify([])
    type_param = (request.args.get("type") or "artist").lower()
    if type_param not in ("artist", "track", "artist,track"):
        type_param = "artist"
    limit = min(10, max(1, int(request.args.get("limit", 8))))
    sp = get_app_spotify()
    if not sp:
        return jsonify({"error": "Spotify unavailable"}), 503
    try:
        results = sp.search(q=q, type=type_param, limit=limit)
        out = []
        if "artists" in results and results["artists"]["items"]:
            for a in results["artists"]["items"]:
                out.append({"type": "artist", "name": a["name"], "id": a["id"]})
        if "tracks" in results and results["tracks"]["items"]:
            for t in results["tracks"]["items"]:
                name = t["name"]
                artist_names = ", ".join(ar["name"] for ar in t["artists"][:3])
                out.append({"type": "track", "name": name, "artist": artist_names, "id": t["id"]})
        return jsonify(out[: limit * 2])
    except Exception:
        return jsonify([])


@bp.route("/recommendations")
@login_required
def recommendations():
    """
    Get personalized track recommendations for the current user (requires Spotify connected).
    Returns a list of suggested tracks based on user's top artists/tracks.
    """
    if not spotify_configured():
        return jsonify({"error": "Spotify not configured"}), 503
    sp = get_spotify_for_user(current_user)
    if not sp:
        return jsonify({"error": "Connect Spotify to get recommendations", "tracks": []}), 200
    out = [None]
    err = [None]

    def _fetch():
        try:
            seed_artists = []
            seed_tracks = []
            top_artists = sp.current_user_top_artists(limit=3)
            for a in top_artists.get("items", []):
                seed_artists.append(a["id"])
            top_tracks = sp.current_user_top_tracks(limit=2)
            for t in top_tracks.get("items", []):
                seed_tracks.append(t["id"])
            seed_a = seed_artists[:2] if seed_artists else None
            seed_t = seed_tracks[:1] if seed_tracks else None
            if not seed_a and not seed_t:
                out[0] = {"tracks": [], "message": "Listen to more music on Spotify to get recommendations."}
                return
            recs = sp.recommendations(seed_artists=seed_a, seed_tracks=seed_t, limit=15)
            tracks = []
            for t in recs.get("tracks", []):
                tracks.append({
                    "name": t["name"],
                    "artist": ", ".join(ar["name"] for ar in t["artists"]),
                    "id": t["id"],
                })
            out[0] = {"tracks": tracks}
        except Exception as e:
            err[0] = e

    th = threading.Thread(target=_fetch)
    th.start()
    th.join(timeout=25)
    if th.is_alive():
        return jsonify({"error": "Spotify took too long. Try again in a moment or check your connection.", "tracks": []}), 200
    if err[0]:
        db.session.rollback()
        return jsonify({"error": "Could not load recommendations", "tracks": []}), 200
    payload = out[0]
    if payload.get("message"):
        return jsonify(payload)
    db.session.commit()
    return jsonify(payload)


@bp.route("/recommendations/artists")
@login_required
def recommendations_artists():
    """
    Return the current user's most listened artists from Spotify (top artists).
    Used to suggest artists when building the artist ranking list.
    """
    if not spotify_configured():
        return jsonify({"error": "Spotify not configured", "artists": []}), 503
    sp = get_spotify_for_user(current_user)
    if not sp:
        return jsonify({"error": "Connect Spotify", "artists": []}), 200
    result, err = [None], [None]

    def _fetch():
        try:
            top = sp.current_user_top_artists(limit=20)
            result[0] = top
        except Exception as e:
            err[0] = e

    th = threading.Thread(target=_fetch)
    th.start()
    th.join(timeout=25)
    if th.is_alive():
        return jsonify({"artists": [], "error": "Spotify took too long. Try again in a moment or check your connection."}), 200
    if err[0]:
        db.session.rollback()
        return jsonify({"artists": [], "error": "Could not load artists"}), 200
    top = result[0]
    artists = [{"name": a["name"], "id": a["id"]} for a in top.get("items", [])]
    db.session.commit()
    return jsonify({"artists": artists})


@bp.route("/recommendations/albums")
@login_required
def recommendations_albums():
    """
    Return albums from the user's most listened tracks + from recommendation seeds.
    Used to suggest albums when building the album ranking list.
    """
    if not spotify_configured():
        return jsonify({"error": "Spotify not configured", "albums": []}), 503
    sp = get_spotify_for_user(current_user)
    if not sp:
        return jsonify({"error": "Connect Spotify", "albums": []}), 200
    result, err = [None], [None]

    def _fetch():
        try:
            seen = set()
            albums = []
            top_tracks = sp.current_user_top_tracks(limit=50)
            for t in top_tracks.get("items", []):
                alb = t.get("album")
                if alb and alb.get("id") and alb["id"] not in seen:
                    seen.add(alb["id"])
                    name = alb.get("name") or "Unknown"
                    artist_names = ", ".join(a["name"] for a in alb.get("artists", [])[:3])
                    albums.append({"name": name, "artist": artist_names, "id": alb["id"]})
            top_artists = sp.current_user_top_artists(limit=2)
            seed_a = [a["id"] for a in top_artists.get("items", [])]
            top_t = sp.current_user_top_tracks(limit=1)
            seed_t = [t["id"] for t in top_t.get("items", [])]
            if seed_a or seed_t:
                recs = sp.recommendations(seed_artists=seed_a[:2] or None, seed_tracks=seed_t[:1] or None, limit=20)
                for t in recs.get("tracks", []):
                    alb = t.get("album")
                    if alb and alb.get("id") and alb["id"] not in seen:
                        seen.add(alb["id"])
                        name = alb.get("name") or "Unknown"
                        artist_names = ", ".join(a["name"] for a in alb.get("artists", [])[:3])
                        albums.append({"name": name, "artist": artist_names, "id": alb["id"]})
            result[0] = albums[:25]
        except Exception as e:
            err[0] = e

    th = threading.Thread(target=_fetch)
    th.start()
    th.join(timeout=25)
    if th.is_alive():
        return jsonify({"albums": [], "error": "Spotify took too long. Try again in a moment or check your connection."}), 200
    if err[0]:
        db.session.rollback()
        return jsonify({"albums": [], "error": "Could not load albums"}), 200
    db.session.commit()
    return jsonify({"albums": result[0]})
