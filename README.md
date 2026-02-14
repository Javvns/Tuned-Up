# Tuned Up

A simple web app to log in and rank your favorite artists. Add artists, drag to reorder, and keep your list in one place.

## Setup

1. Create and activate a virtual environment (optional but recommended):

   ```bash
   cd Tuned-Up
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   python run.py
   ```

   Or with Flask’s CLI:

   ```bash
   export FLASK_APP=app
   flask run
   ```

4. Open [http://127.0.0.1:5001](http://127.0.0.1:5001) in your browser (app runs on port 5001).

### Spotify (optional)

To enable artist/song suggestions and personalized recommendations:

1. Create an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard). Add a **Redirect URI** (e.g. `http://127.0.0.1:5001/auth/spotify/callback`).
2. Set environment variables (or a `.env` file if you load it in your app):
   - `SPOTIFY_CLIENT_ID` – your app’s Client ID  
   - `SPOTIFY_CLIENT_SECRET` – your app’s Client Secret  
   - `SPOTIFY_REDIRECT_URI` – must match the redirect URI in the dashboard (e.g. `http://127.0.0.1:5001/auth/spotify/callback`)
3. **Suggestions** (artist/song search while typing) work with only these credentials.
4. **Recommendations** require users to click “Connect Spotify” and authorize the app (OAuth). The app uses the `user-top-read` scope to seed recommendations from their top artists and tracks.

## Features

- **Sign up / Log in** – Create an account or log in with username and password.
- **Artist / Album / Song rankings** – Add items, drag to reorder, remove with ×.
- **Spotify suggestions** – Start typing in Artists or Songs to see suggestions from Spotify; click to fill and add.
- **Connect Spotify** – Log in with Spotify (sidebar) to get personalized song recommendations based on your listening.
- **Persistent list** – Your rankings are stored per account in SQLite.

## Tech

- **Backend:** Flask, Flask-Login, Flask-SQLAlchemy, SQLite  
- **Frontend:** Jinja2 templates, vanilla JS, CSS
