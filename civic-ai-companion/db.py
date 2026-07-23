"""
SQLite helpers for the complaint filing + tracking system.
Uses your existing SQL skills instead of Firebase - same functionality,
familiar tech.
"""

import sqlite3
import uuid
from datetime import datetime

DB_PATH = "civic_complaints.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            category TEXT,
            status TEXT DEFAULT 'Received',
            filed_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def file_complaint(description: str, location: str, category: str) -> str:
    complaint_id = str(uuid.uuid4())[:8].upper()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO complaints (id, description, location, category, status, filed_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (complaint_id, description, location, category, "Received", datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return complaint_id


def get_complaint(complaint_id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "id": row[0],
        "description": row[1],
        "location": row[2],
        "category": row[3],
        "status": row[4],
        "filed_at": row[5],
    }


def update_status(complaint_id: str, new_status: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE complaints SET status = ? WHERE id = ?", (new_status, complaint_id))
    conn.commit()
    conn.close()
