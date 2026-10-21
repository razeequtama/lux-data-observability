"""Validations API router exposing execution and findings inspection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.validation import (
    ValidationFindingItem,
    ValidationFindingsListResponse,
    ValidationRunRequest,
    ValidationRunResponse,
)
from app.services.validation.runner import ValidationRunnerService

router = APIRouter(prefix="/validations", tags=["Validations"])


@router.post(
    "/run",
    response_model=ValidationRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Validation Run",
    description="Execute data quality validation rules against datasets and persist findings.",
)
def execute_validation_run(
    payload: ValidationRunRequest,
    db: Session = Depends(get_db),
) -> ValidationRunResponse:
    """Execute quality validations for a scenario."""
    run = ValidationRunnerService.execute_validation_run(
        scenario_id=payload.scenario_id,
        db=db,
        dataset_ids=payload.dataset_ids,
    )
    return ValidationRunResponse.from_model(run)


@router.get(
    "/runs/{run_id}",
    response_model=ValidationRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Validation Run Summary",
    description="Retrieve execution metrics and status for a specific validation run.",
)
def get_validation_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> ValidationRunResponse:
    """Get validation run summary by ID."""
    run = ValidationRunnerService.get_validation_run(run_id=run_id, db=db)
    return ValidationRunResponse.from_model(run)


@router.get(
    "/runs",
    response_model=list[ValidationRunResponse],
    status_code=status.HTTP_200_OK,
    summary="List Validation Runs",
    description="List historical validation runs, optionally filtered by scenario ID.",
)
def list_validation_runs(
    scenario_id: str | None = Query(default=None, description="Filter by scenario ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Page size limit"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
) -> list[ValidationRunResponse]:
    """List validation runs."""
    _, runs = ValidationRunnerService.list_validation_runs(
        db=db,
        scenario_id=scenario_id,
        limit=limit,
        offset=offset,
    )
    return [ValidationRunResponse.from_model(r) for r in runs]


@router.get(
    "/runs/{run_id}/findings",
    response_model=ValidationFindingsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Validation Findings",
    description="Retrieve granular findings for a run with optional filtering and pagination.",
)
def list_validation_findings(
    run_id: str,
    severity: str | None = Query(default=None, description="Filter by finding severity"),
    status: str | None = Query(default=None, description="Filter by rule outcome status"),
    dataset_id: str | None = Query(default=None, description="Filter by dataset identifier"),
    limit: int = Query(default=50, ge=1, le=500, description="Page size limit"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
) -> ValidationFindingsListResponse:
    """Retrieve filterable findings for a specific validation run."""
    total, findings = ValidationRunnerService.list_run_findings(
        run_id=run_id,
        db=db,
        severity=severity,
        status=status,
        dataset_id=dataset_id,
        limit=limit,
        offset=offset,
    )
    items = [ValidationFindingItem.from_model(f) for f in findings]
    return ValidationFindingsListResponse(
        run_id=run_id,
        total_findings=total,
        items=items,
    )
