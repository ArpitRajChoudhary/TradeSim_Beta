
import copy
import json
import uuid

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock

import auth
from ai_backtest import run_ai_backtest


executor = ThreadPoolExecutor(max_workers=2)

JOBS_LOCK = Lock()
INITIALIZATION_LOCK = Lock()
DATABASE_INITIALIZED = False


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def initialize_jobs_database():
    global DATABASE_INITIALIZED

    with INITIALIZATION_LOCK:
        if DATABASE_INITIALIZED:
            return

        auth.initialize_database()

        with auth.get_connection() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS backtest_jobs (
                    run_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    execution_time_seconds REAL,
                    candles_processed INTEGER,
                    dataset TEXT,
                    config TEXT NOT NULL,
                    results TEXT,
                    error TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_backtest_jobs_user_created
                ON backtest_jobs(user_id, created_at)
            """)

            connection.execute("""
                UPDATE backtest_jobs
                SET
                    status = 'failed',
                    completed_at = ?,
                    error = 'Backtest interrupted by backend restart.'
                WHERE status IN ('queued', 'running')
            """, (utc_now(),))

            connection.commit()

        DATABASE_INITIALIZED = True

def serialize_job(job):
    return (
        job["run_id"],
        job["user_id"],
        job["status"],
        job["created_at"],
        job["started_at"],
        job["completed_at"],
        job["execution_time_seconds"],
        job["candles_processed"],
        job["dataset"],
        json.dumps(job["config"]),
        json.dumps(job["results"]) if job["results"] is not None else None,
        job["error"],
    )


def deserialize_job(row):
    job = dict(row)

    job["config"] = json.loads(job["config"])
    job["results"] = (
        json.loads(job["results"])
        if job["results"] is not None
        else None
    )

    return job


def save_job(job):
    values = serialize_job(job)

    with auth.get_connection() as connection:
        connection.execute("""
            INSERT OR REPLACE INTO backtest_jobs (
                run_id,
                user_id,
                status,
                created_at,
                started_at,
                completed_at,
                execution_time_seconds,
                candles_processed,
                dataset,
                config,
                results,
                error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)

        connection.commit()


def update_job(run_id, updates):
    allowed_fields = {
        "status",
        "started_at",
        "completed_at",
        "execution_time_seconds",
        "candles_processed",
        "dataset",
        "results",
        "error",
    }

    if not set(updates).issubset(allowed_fields):
        raise ValueError("Invalid backtest job update.")

    assignments = []
    values = []

    for field, value in updates.items():
        if field == "results" and value is not None:
            value = json.dumps(value)

        assignments.append(f"{field} = ?")
        values.append(value)

    if not assignments:
        return

    values.append(run_id)

    with auth.get_connection() as connection:
        connection.execute(
            f"""
            UPDATE backtest_jobs
            SET {", ".join(assignments)}
            WHERE run_id = ?
            """,
            values,
        )

        connection.commit()


def execute_job(run_id, config):
    with JOBS_LOCK:
        update_job(run_id, {
            "status": "running",
            "started_at": utc_now(),
        })

    try:
        execution = run_ai_backtest(
            config,
            generate_report=False,
        )

        update_job(run_id, {
            "status": "completed",
            "completed_at": utc_now(),
            "execution_time_seconds": (
                execution["execution_time_seconds"]
            ),
            "candles_processed": execution["candles_processed"],
            "dataset": execution["dataset"],
            "results": execution["results"],
            "error": None,
        })

    except Exception as error:
        update_job(run_id, {
            "status": "failed",
            "completed_at": utc_now(),
            "error": str(error),
        })


def start_backtest(config, user_id):
    initialize_jobs_database()

    run_id = str(uuid.uuid4())

    job = {
        "run_id": run_id,
        "user_id": user_id,
        "status": "queued",
        "created_at": utc_now(),
        "started_at": None,
        "completed_at": None,
        "execution_time_seconds": None,
        "candles_processed": None,
        "dataset": None,
        "config": copy.deepcopy(config),
        "results": None,
        "error": None,
    }

    with JOBS_LOCK:
        save_job(job)

    executor.submit(
        execute_job,
        run_id,
        copy.deepcopy(config),
    )

    return get_backtest(run_id, user_id)


def get_backtest(run_id, user_id):
    initialize_jobs_database()

    with auth.get_connection() as connection:
        row = connection.execute("""
            SELECT *
            FROM backtest_jobs
            WHERE run_id = ? AND user_id = ?
        """, (
            run_id,
            user_id,
        )).fetchone()

    if row is None:
        return None

    return deserialize_job(row)


def get_all_backtests(user_id):
    initialize_jobs_database()

    with auth.get_connection() as connection:
        rows = connection.execute("""
            SELECT *
            FROM backtest_jobs
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (
            user_id,
        )).fetchall()

    return [
        deserialize_job(row)
        for row in rows
    ]


initialize_jobs_database()
