import json
import os
from contextlib import contextmanager
import psycopg2

def connect():
    url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("POSTGRES_URL is not set")
    return psycopg2.connect(url)

@contextmanager
def cursor():
    conn = connect()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    finally:
        conn.close()

SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    headlines TEXT NOT NULL,
    analysis TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES analyses(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    trend TEXT,
    forecast TEXT,
    confidence TEXT,
    check_days INTEGER,
    status TEXT NOT NULL DEFAULT 'open',
    verdict_at TIMESTAMPTZ,
    evidence TEXT
);
CREATE TABLE IF NOT EXISTS seen_headlines (
    title TEXT PRIMARY KEY,
    link TEXT,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

def init_schema():
    with cursor() as cur:
        cur.execute(SCHEMA)

def record_headlines(items):
    with cursor() as cur:
        for title, link in items:
            cur.execute(
                "INSERT INTO seen_headlines (title, link) VALUES (%s, %s) ON CONFLICT (title) DO NOTHING",
                (title, link),
            )

def save_analysis(headlines, analysis):
    with cursor() as cur:
        cur.execute(
            "INSERT INTO analyses (headlines, analysis) VALUES (%s, %s) RETURNING id",
            (json.dumps(headlines), analysis),
        )
        return cur.fetchone()[0]

def save_predictions(analysis_id, preds):
    with cursor() as cur:
        for p in preds:
            cur.execute(
                "INSERT INTO predictions (analysis_id, trend, forecast, confidence, check_days) "
                "VALUES (%s, %s, %s, %s, %s)",
                (analysis_id, p["trend"], p["forecast"], p["confidence"], p["check_days"]),
            )

def list_analyses(limit=10):
    with cursor() as cur:
        cur.execute("SELECT id, created_at, analysis FROM analyses ORDER BY id DESC LIMIT %s", (limit,))
        return [(i, c.isoformat(timespec="seconds"), a) for i, c, a in cur.fetchall()]

def list_predictions(limit=30):
    with cursor() as cur:
        cur.execute(
            "SELECT id, analysis_id, trend, forecast, confidence, check_days, status, COALESCE(evidence, '') "
            "FROM predictions ORDER BY id DESC LIMIT %s",
            (limit,),
        )
        return cur.fetchall()

def due_predictions():
    with cursor() as cur:
        cur.execute(
            "SELECT id, trend, forecast, created_at, created_at + make_interval(days => check_days) AS end_at "
            "FROM predictions WHERE status = 'open' "
            "AND created_at + make_interval(days => check_days) <= now()"
        )
        return cur.fetchall()

def later_headlines(start, end, limit=150):
    with cursor() as cur:
        cur.execute(
            "SELECT title FROM seen_headlines WHERE first_seen > %s AND first_seen <= %s "
            "ORDER BY first_seen LIMIT %s",
            (start, end, limit),
        )
        return cur.fetchall()

def record_verdict(pid, status, evidence):
    with cursor() as cur:
        cur.execute(
            "UPDATE predictions SET status = %s, verdict_at = now(), evidence = %s WHERE id = %s",
            (status, evidence, pid),
        )
