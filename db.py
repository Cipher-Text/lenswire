import sqlite3
from contextlib import contextmanager

from config import DB_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                interests TEXT DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_articles (
                chat_id INTEGER,
                article_url TEXT,
                PRIMARY KEY (chat_id, article_url)
            )
            """
        )


def upsert_user(chat_id):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))


def set_interests(chat_id, interests_str):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (chat_id, interests) VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET interests=excluded.interests
            """,
            (chat_id, interests_str),
        )


def get_interests(chat_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT interests FROM users WHERE chat_id=?", (chat_id,)
        ).fetchone()
        return row[0] if row else ""


def get_all_users():
    """Returns list of (chat_id, interests) for users who have set interests."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT chat_id, interests FROM users WHERE interests != ''"
        ).fetchall()


def was_sent(chat_id, url):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM sent_articles WHERE chat_id=? AND article_url=?",
            (chat_id, url),
        ).fetchone()
        return row is not None


def mark_sent(chat_id, url):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_articles (chat_id, article_url) VALUES (?, ?)",
            (chat_id, url),
        )
