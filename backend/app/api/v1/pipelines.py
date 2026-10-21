"""Pipelines API router exposing run history and execution vs quality dual-dimension tracking."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.pipeline import PipelineRunResponse
from app.services.pipeline.service import PipelineHistoryService

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])


@router.get(
    "/runs",
    response_model=list[PipelineRunResponse],
    status_code=status.HTTP_200_OK,
    summary="List Pipeline Runs",
    description=(
        "Retrieve historical pipeline runs with duration, records processed, "
        "step logs, and dual-dimension status (Compute Execution vs Data Quality Health)."
    ),
)
def list_pipeline_runs(
    scenario_id: str | None = Query(
        default=None, description="Filter pipeline runs by scenario ID"
    ),
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum number of runs to return"),
    offset: int = Query(default=0, ge=0, description="Number of runs to skip for pagination"),
    include_logs: bool = Query(default=True, description="Whether to parse and include step logs"),
    db: Session = Depends(get_db),
) -> list[PipelineRunResponse]:
    """Retrieve historical pipeline runs sorted descending by execution start time."""
    runs = PipelineHistoryService.get_runs(
        db=db,
        scenario_id=scenario_id,
        limit=limit,
        offset=offset,
    )
    return [PipelineRunResponse.from_model(run, include_logs=include_logs) for run in runs]


@router.get(
    "/runs/{run_id}",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Pipeline Run Detail",
    description=(
        "Retrieve detailed execution metrics, dual-dimension health badges, "
        "and step logs for a specific pipeline run."
    ),
)
def get_pipeline_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> PipelineRunResponse:
    """Retrieve a single pipeline run by its unique identifier."""
    run = PipelineHistoryService.get_run_by_id(db=db, run_id=run_id)
    return PipelineRunResponse.from_model(run, include_logs=True)
