"""
Creates all tables against the configured DATABASE_URL.

Run this explicitly once (and again after adding new models) — it is NOT
called automatically on app startup. Keeping it explicit means:
  - starting the app/running tests never silently depends on a live DB
  - you get a clear moment where you know the schema changed

Usage:
    uv run python -m scripts.init_db

This is an MVP stand-in for real migrations. Once the schema needs to
change without losing data (e.g. adding a column to a table with existing
rows), replace this with Alembic — create_all() only ever adds missing
tables, it never alters existing ones. Flagging this now as a known
limitation, not fixing it preemptively before we actually need migrations.
"""
from app.db import init_db

if __name__ == "__main__":
    init_db()
    print("Tables created (or already existed).")
