import sqlite3
from datetime import datetime

DB_NAME = "submissions.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Заявки
    cur.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        full_name TEXT,

        music_type TEXT,
        file_id TEXT,
        image_file_id TEXT,
        link TEXT,

        title TEXT,
        artist TEXT,
        comment TEXT,

        status TEXT DEFAULT 'pending',

        created_at TEXT,
        approved_at TEXT
    )
    """)

    # Опубліковані треки
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tracks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        title TEXT NOT NULL,
        artist TEXT NOT NULL,

        file_id TEXT,
        file_unique_id TEXT,

        link TEXT,
        comment TEXT,

        user_id INTEGER,
        submission_id INTEGER,

        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_submission(data: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO submissions(
            user_id,
            username,
            full_name,

            music_type,
            file_id,
            image_file_id,
            link,

            title,
            artist,
            comment,

            created_at
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            data["user_id"],
            data["username"],
            data["full_name"],
            data["music_type"],
            data.get("file_id"),
            data.get("image_file_id"),
            data.get("link"),
            data["title"],
            data["artist"],
            data.get("comment"),
            datetime.now().isoformat(),
        ),
    )

    submission_id = cur.lastrowid

    conn.commit()
    conn.close()

    return submission_id


def get_submission(submission_id):
    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM submissions WHERE id=?",
        (submission_id,),
    ).fetchone()

    conn.close()

    return row


def approve_submission(submission_id):
    conn = get_connection()

    conn.execute(
        """
        UPDATE submissions
        SET status='approved',
            approved_at=?
        WHERE id=?
        """,
        (
            datetime.now().isoformat(),
            submission_id,
        ),
    )

    conn.commit()
    conn.close()


def reject_submission(submission_id):
    conn = get_connection()

    conn.execute(
        """
        UPDATE submissions
        SET status='rejected'
        WHERE id=?
        """,
        (submission_id,),
    )

    conn.commit()
    conn.close()


def get_pending():
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM submissions
        WHERE status='pending'
        ORDER BY id ASC
        """
    ).fetchall()

    conn.close()

    return rows


def get_stats():
    conn = get_connection()

    total = conn.execute(
        "SELECT COUNT(*) FROM submissions"
    ).fetchone()[0]

    pending = conn.execute(
        "SELECT COUNT(*) FROM submissions WHERE status='pending'"
    ).fetchone()[0]

    approved = conn.execute(
        "SELECT COUNT(*) FROM submissions WHERE status='approved'"
    ).fetchone()[0]

    rejected = conn.execute(
        "SELECT COUNT(*) FROM submissions WHERE status='rejected'"
    ).fetchone()[0]

    conn.close()

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
    }


# ==========================================================
# TRACKS
# ==========================================================

def save_track(data: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tracks(
            title,
            artist,
            file_id,
            file_unique_id,
            link,
            comment,
            user_id,
            submission_id,
            created_at
        )
