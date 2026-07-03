import sqlite3
import os

DB_FILE = "bot_data.db"

def get_db_connection():
    """Create a database connection and return it."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database tables if they do not exist."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_keys (
                user_id INTEGER PRIMARY KEY,
                gemini_api_key TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()

def set_user_key(user_id: int, key: str) -> None:
    """Insert or update a Gemini API key for a specific user."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_keys (user_id, gemini_api_key, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                gemini_api_key = excluded.gemini_api_key,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, key))
        conn.commit()
    finally:
        conn.close()

def get_user_key(user_id: int) -> str | None:
    """Retrieve the Gemini API key for a user, or None if not set."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT gemini_api_key FROM user_keys WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return row["gemini_api_key"]
        return None
    finally:
        conn.close()

def delete_user_key(user_id: int) -> bool:
    """Delete a user's API key. Returns True if a key was deleted, False otherwise."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_keys WHERE user_id = ?", (user_id,))
        changes = conn.total_changes
        conn.commit()
        return changes > 0
    finally:
        conn.close()
