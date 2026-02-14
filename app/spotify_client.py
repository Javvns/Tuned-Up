"""
Spotify API helpers: app-level token for search, user-level OAuth for recommendations.
"""
import os
import threading
import time
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from spotipy.cache_handler import CacheHandler

REFRESH_TIMEOUT_SEC = 10


def get_spotify_config():
    return {
        "client_id": os.environ.get("SPOTIFY_CLIENT_ID", ""),
        "client_secret": os.environ.get("SPOTIFY_CLIENT_SECRET", ""),
        "redirect_uri": os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5001/auth/spotify/callback"),
    }


def spotify_configured():
    cfg = get_spotify_config()
    return bool(cfg["client_id"] and cfg["client_secret"])


class UserTokenCache(CacheHandler):
    """CacheHandler that stores token in the User model for spotipy OAuth refresh."""

    def __init__(self, user):
        self.user = user

    def get_cached_token(self):
        if not self.user or not self.user.spotify_refresh_token:
            return None
        now = int(time.time())
        # Return valid access token if we have one and it's not expired (with 60s buffer)
        if (
            getattr(self.user, "spotify_access_token", None)
            and getattr(self.user, "spotify_token_expires_at", None)
            and self.user.spotify_token_expires_at - 60 > now
        ):
            return {
                "access_token": self.user.spotify_access_token,
                "refresh_token": self.user.spotify_refresh_token,
                "expires_at": self.user.spotify_token_expires_at,
            }
        return {"refresh_token": self.user.spotify_refresh_token, "expires_at": 0}

    def save_token_to_cache(self, token_info):
        if not self.user:
            return
        if token_info.get("access_token"):
            self.user.spotify_access_token = token_info["access_token"]
        if token_info.get("expires_at"):
            self.user.spotify_token_expires_at = token_info["expires_at"]
        if token_info.get("refresh_token"):
            self.user.spotify_refresh_token = token_info["refresh_token"]


def get_spotify_oauth(redirect_uri=None):
    cfg = get_spotify_config()
    if not cfg["client_id"] or not cfg["client_secret"]:
        return None
    return SpotifyOAuth(
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        redirect_uri=redirect_uri or cfg["redirect_uri"],
        scope="user-top-read",
        open_browser=False,
        requests_timeout=12,
    )


def _user_has_valid_token(user):
    """True if user has a non-expired access token (with 60s buffer)."""
    if not user:
        return False
    exp = getattr(user, "spotify_token_expires_at", None)
    if not exp or not getattr(user, "spotify_access_token", None):
        return False
    return int(time.time()) < exp - 60


def _clear_user_spotify_tokens(user):
    """Clear stored Spotify tokens so user must reconnect."""
    if not user:
        return
    user.spotify_refresh_token = None
    user.spotify_access_token = None
    user.spotify_token_expires_at = None


def get_spotify_for_user(user):
    """Return a Spotipy client for the given user (for recommendations). Uses refresh token."""
    if not user or not user.spotify_refresh_token:
        return None
    cfg = get_spotify_config()
    if not cfg["client_id"] or not cfg["client_secret"]:
        return None
    cache = UserTokenCache(user)
    auth = SpotifyOAuth(
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        redirect_uri=cfg["redirect_uri"],
        scope="user-top-read",
        open_browser=False,
        cache_handler=cache,
        requests_timeout=12,
    )
    # If we already have a valid token, no need to refresh; return client.
    if _user_has_valid_token(user):
        return Spotify(auth_manager=auth, requests_timeout=15)
    # Otherwise refresh first with a short timeout so we don't hang.
    err = [None]

    def _do_refresh():
        try:
            auth.get_access_token(code=None, as_dict=True, check_cache=True)
        except Exception as e:
            err[0] = e

    th = threading.Thread(target=_do_refresh)
    th.start()
    th.join(timeout=REFRESH_TIMEOUT_SEC)
    if th.is_alive():
        # Refresh is still running; return None so caller can show "try again" / reconnect.
        return None
    if err[0]:
        _clear_user_spotify_tokens(user)
        return None
    return Spotify(auth_manager=auth, requests_timeout=15)


_app_client = None
_app_token_expires = 0


def get_app_spotify():
    """Client Credentials client for search (no user login). Cached and refreshed."""
    global _app_client, _app_token_expires
    cfg = get_spotify_config()
    if not cfg["client_id"] or not cfg["client_secret"]:
        return None
    if _app_client is not None and time.time() < _app_token_expires - 60:
        return _app_client
    try:
        auth = SpotifyClientCredentials(
            client_id=cfg["client_id"],
            client_secret=cfg["client_secret"],
        )
        _app_client = Spotify(auth_manager=auth, requests_timeout=15)
        _app_token_expires = time.time() + 3600
        return _app_client
    except Exception:
        return None
