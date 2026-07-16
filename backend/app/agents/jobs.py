"""
PatentPilot job manager.

Tracks analysis jobs in-memory while the backend completes long-running processing.
This is intentionally lightweight and suitable for local development.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

_job_store: dict[str, dict[str, Any]] = {}
_job_lock = asyncio.Lock()


def _new_job_entry(request_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "status": "pending",
        "request": request_data,
        "analysis_id": None,
        "error": None,
        "created_at": None,
        "updated_at": None,
    }


async def create_job(request_data: dict[str, Any]) -> str:
    async with _job_lock:
        job = _new_job_entry(request_data)
        _job_store[job["id"]] = job
        logger.info("Created analysis job %s", job["id"])
        return job["id"]


async def update_job_status(job_id: str, status: str, payload: Any | None = None) -> None:
    async with _job_lock:
        job = _job_store.get(job_id)
        if not job:
            return

        job["status"] = status
        if status == "completed":
            job["analysis_id"] = str(payload) if payload is not None else None
        elif status == "failed":
            job["error"] = str(payload)

        logger.info("Job %s status updated to %s", job_id, status)


async def get_job(job_id: str) -> dict[str, Any] | None:
    async with _job_lock:
        return _job_store.get(job_id)
