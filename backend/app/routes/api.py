"""
PatentPilot API Routes.

Defines the REST endpoints for patent analysis.
"""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.models.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisListItem,
)
from app.agents import coordinator, history, jobs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


async def _background_analysis(job_id: str, request: AnalysisRequest) -> None:
    try:
        result = await coordinator.run_pipeline(request)
        if result is None or not isinstance(result, dict):
            raise RuntimeError("Analysis pipeline returned an unexpected value")
        analysis_id = result.get("id")
        if not analysis_id:
            raise RuntimeError("Analysis pipeline did not persist result id")
        await jobs.update_job_status(job_id, "completed", analysis_id)
    except Exception as exc:
        logger.exception("Job %s failed during processing: %s", job_id, exc)
        await jobs.update_job_status(job_id, "failed", str(exc))


@router.post("/analyze", status_code=202)
async def analyze_molecule(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """
    Accept a new analysis request and enqueue it for asynchronous processing.

    Returns a job ID immediately so the frontend can poll for completion.
    """
    logger.info(
        "POST /api/analyze — SMILES=%s, target=%s, disease=%s",
        request.smiles[:50],
        request.target,
        request.disease,
    )
    job_id = await jobs.create_job(request.dict())
    background_tasks.add_task(_background_analysis, job_id, request)
    return {"job_id": job_id}


@router.get("/job-status/{job_id}")
async def get_job_status(job_id: str) -> dict[str, Any]:
    job = await jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": job["id"],
        "status": job["status"],
        "analysis_id": job.get("analysis_id"),
        "error": job["error"],
    }


@router.get("/analyses", response_model=list[AnalysisListItem])
async def list_analyses() -> list[dict[str, Any]]:
    """Return a summary list of all past analyses, newest first."""
    try:
        return await history.list_analyses()
    except Exception as exc:
        logger.exception("Failed to list analyses: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve analyses: {exc}",
        )


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str) -> dict[str, Any]:
    """Retrieve a single analysis by its ID."""
    try:
        result = await history.get_analysis(analysis_id)
    except Exception as exc:
        logger.exception("Failed to fetch analysis %s: %s", analysis_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve analysis: {exc}",
        )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis with id '{analysis_id}' not found.",
        )
    return result
