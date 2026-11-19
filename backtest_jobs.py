
import copy
import uuid

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock

from ai_backtest import run_ai_backtest


executor = ThreadPoolExecutor(max_workers=2)

JOBS = {}
JOBS_LOCK = Lock()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def execute_job(run_id, config):
    with JOBS_LOCK:
        JOBS[run_id]["status"] = "running"
        JOBS[run_id]["started_at"] = utc_now()

    try:
        execution = run_ai_backtest(
            config,
            generate_report=False,
        )

        with JOBS_LOCK:
            JOBS[run_id].update({
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
        with JOBS_LOCK:
            JOBS[run_id].update({
                "status": "failed",
                "completed_at": utc_now(),
                "error": str(error),
            })


def start_backtest(config):
    run_id = str(uuid.uuid4())

    with JOBS_LOCK:
        JOBS[run_id] = {
            "run_id": run_id,
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

    executor.submit(
        execute_job,
        run_id,
        copy.deepcopy(config),
    )

    return get_backtest(run_id)


def get_backtest(run_id):
    with JOBS_LOCK:
        job = JOBS.get(run_id)

        if job is None:
            return None

        return copy.deepcopy(job)
