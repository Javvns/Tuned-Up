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

4. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Features

- **Sign up / Log in** – Create an account or log in with username and password.
- **Artist rankings** – Add artists by name. Drag rows to reorder your list. Remove artists with the × button.
- **Persistent list** – Your rankings are stored per account in SQLite.

## Tech

- **Backend:** Flask, Flask-Login, Flask-SQLAlchemy, SQLite  
- **Frontend:** Jinja2 templates, vanilla JS, CSS
