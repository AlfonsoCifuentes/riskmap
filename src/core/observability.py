"""Lightweight pipeline observability (spec §22 / §107, addendum).

Records one row per pipeline stage run into `pipeline_runs` so the System
Observatory / Pipeline Run Explorer can show what ran, when, in/out counts and
status. Best-effort: if the table or DB is unavailable it degrades to a log line
and never breaks the pipeline.

A single INSERT at completion (not insert-then-update) keeps it backend-agnostic
(no RETURNING / lastrowid juggling).
"""
from __future__ import annotations

import contextlib
import logging
import os
import time
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def pipeline_run(stage: str, items_in: int = 0):
    """Context manager timing a pipeline stage.

    Usage:
        with pipeline_run("enrich", items_in=n) as stats:
            ...
            stats["items_out"] = processed
    """
    start = time.time()
    stats = {"items_out": 0, "errors": 0, "notes": None}
    status = "success"
    try:
        yield stats
    except Exception as exc:  # noqa: BLE001 — record then re-raise
        status = "failed"
        stats["errors"] = stats.get("errors", 0) + 1
        stats["notes"] = str(exc)[:500]
        raise
    finally:
        _record(stage, start, status, items_in, stats)


def _record(stage, start_ts, status, items_in, stats):
    try:
        from src.database.connection import _detect_backend, get_db
        db = get_db()
        ph = "%s" if _detect_backend() == "postgres" else "?"
        started = datetime.fromtimestamp(start_ts, UTC)
        finished = datetime.now(UTC)
        db.execute(
            f"""INSERT INTO pipeline_runs
                (stage, started_at, finished_at, status, items_in, items_out,
                 errors, git_sha, notes)
                VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
            (
                stage, started, finished, status,
                int(items_in), int(stats.get("items_out", 0)),
                int(stats.get("errors", 0)),
                os.getenv("GITHUB_SHA") or os.getenv("VERCEL_GIT_COMMIT_SHA"),
                stats.get("notes"),
            ),
        )
        logger.info("pipeline_run recorded: %s status=%s in=%s out=%s",
                    stage, status, items_in, stats.get("items_out", 0))
    except Exception as e:  # noqa: BLE001 — observability must never break the run
        logger.debug("pipeline_run not recorded (%s): %s", stage, e)
