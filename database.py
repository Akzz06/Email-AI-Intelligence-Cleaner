# database.py

import sqlite3
from datetime import datetime

DB_NAME = "emails.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id TEXT PRIMARY KEY,
        subject TEXT,
        sender TEXT,
        body TEXT,
        category TEXT,
        size INTEGER,
        datetime TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS deleted_emails (
        id TEXT PRIMARY KEY,
        size INTEGER,
        deleted_at TEXT
    )
    """)

    # --- THIS TABLE IS REPLACED ---
    # We no longer need deletion_queue
    c.execute("DROP TABLE IF EXISTS deletion_queue")

    # --- THIS IS THE NEW JOBS TABLE ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_type TEXT NOT NULL,
        parameters TEXT,
        status TEXT DEFAULT 'PENDING',
        progress_message TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

# --- NEW FUNCTION TO CREATE A JOB ---
def create_job(job_type, parameters="{}"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    INSERT INTO jobs (job_type, parameters, status, created_at)
    VALUES (?, ?, 'PENDING', ?)
    """, (job_type, parameters, datetime.now().isoformat()))
    job_id = c.lastrowid
    conn.commit()
    conn.close()
    return job_id

# --- HELPER FUNCTIONS FOR THE WORKER ---
def get_next_job():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE status = 'PENDING' ORDER BY created_at ASC LIMIT 1")
    job = c.fetchone()
    if job:
        # Mark job as RUNNING
        c.execute("UPDATE jobs SET status = 'RUNNING' WHERE id = ?", (job['id'],))
        conn.commit()
        conn.close()
        return dict(job)
    conn.close()
    return None

def update_job_progress(job_id, message):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE jobs SET progress_message = ? WHERE id = ?", (message, job_id))
    conn.commit()
    conn.close()

def mark_job_done(job_id, message="Completed"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE jobs SET status = 'DONE', progress_message = ? WHERE id = ?", (message, job_id))
    conn.commit()
    conn.close()

def mark_job_failed(job_id, error_message):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE jobs SET status = 'FAILED', progress_message = ? WHERE id = ?", (error_message, job_id))
    conn.commit()
    conn.close()


# --- (All other functions like save_email, get_all_emails, etc. stay the same) ---

def email_exists(msg_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM emails WHERE id = ?", (msg_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists


def save_email(email):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    INSERT OR IGNORE INTO emails 
    (id, subject, sender, body, category, size, datetime)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        email["id"], email["subject"], email["sender"],
        email["body"], email.get("category"), email["size"],
        email["datetime"]
    ))
    conn.commit()
    conn.close()


def get_all_emails():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM emails ORDER BY datetime ASC")
    rows = c.fetchall()
    conn.close()
    return rows


def delete_email_from_db(msg_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT size FROM emails WHERE id = ?", (msg_id,))
    row = c.fetchone()
    if row:
        size = row[0]
        c.execute("""
        INSERT OR REPLACE INTO deleted_emails (id, size, deleted_at)
        VALUES (?, ?, ?)
        """, (msg_id, size, datetime.now().isoformat()))
        c.execute("DELETE FROM emails WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()


def get_storage_saved():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT SUM(size) FROM deleted_emails")
    total = c.fetchone()[0]
    conn.close()
    return (total or 0) / 1_000_000


def get_oldest_datetime():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT datetime FROM emails ORDER BY datetime ASC LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row[0] if row else None