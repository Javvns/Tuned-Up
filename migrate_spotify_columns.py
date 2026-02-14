"""
One-time migration: add spotify_id and spotify_refresh_token to the users table.
Run from project root: python migrate_spotify_columns.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tunedup.db")

if not os.path.exists(DB_PATH):
    print("No tunedup.db found. Run the app once to create it, then run this script.")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get existing columns
cur.execute("PRAGMA table_info(users)")
columns = [row[1] for row in cur.fetchall()]

if "spotify_id" not in columns:
    cur.execute("ALTER TABLE users ADD COLUMN spotify_id VARCHAR(80)")
    print("Added column: spotify_id")
else:
    print("Column spotify_id already exists")

if "spotify_refresh_token" not in columns:
    cur.execute("ALTER TABLE users ADD COLUMN spotify_refresh_token VARCHAR(256)")
    print("Added column: spotify_refresh_token")
else:
    print("Column spotify_refresh_token already exists")

conn.commit()
conn.close()
print("Done.")
