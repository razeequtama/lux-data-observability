"""API router for investigation workspace management and hypothesis tracking."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.investigation import (
    InvestigationCreateRequest,
    InvestigationResponse,
    InvestigationSynthesizeRequest,
    InvestigationUpdateRequest,
)
from app.services.reports.investigation import InvestigationService

router = APIRouter(prefix="/investigations", tags=["Investigations"])


@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Investigation Workspace",
    description=(
        "Initialize a new investigation workspace separating verified facts, "
        "hypotheses, and action items."
    ),
)
def create_investigation(
    payload: InvestigationCreateRequest,
    db: Session = Depends(get_db),
) -> InvestigationResponse:
    """Create an investigation workspace."""
    investigation = InvestigationService.create_investigation(db=db, request=payload)
    return InvestigationResponse.from_model(investigation)


@router.get(
    "/{investigation_id}",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Investigation Workspace",
    description="Retrieve an investigation workspace by unique identifier.",
)
def get_investigation(
    investigation_id: str,
    db: Session = Depends(get_db),
) -> InvestigationResponse:
    """Retrieve investigation by ID."""
    investigation = InvestigationService.get_investigation(db=db, investigation_id=investigation_id)
    return InvestigationResponse.from_model(investigation)


@router.get(
    "",
    response_model=list[InvestigationResponse],
    status_code=status.HTTP_200_OK,
    summary="List Investigation Workspaces",
    description=(
        "Retrieve a list of investigation workspaces with optional scenario and status filters."
    ),
)
def list_investigations(
    scenario_id: str | None = Query(None, description="Filter by scenario ID"),
    investigation_status: str | None = Query(
        None, alias="status", description="Filter by investigation status"
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
) -> list[InvestigationResponse]:
    """List investigations."""
    items, _ = InvestigationService.list_investigations(
        db=db,
        scenario_id=scenario_id,
        status=investigation_status,
        limit=limit,
        offset=offset,
    )
    return [InvestigationResponse.from_model(item) for item in items]


@router.patch(
    "/{investigation_id}",
    response_model=InvestigationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Investigation Workspace",
    description=(
        "Update investigation title, lifecycle status, verified facts, hypotheses, or action items."
    ),
)
def update_investigation(
    investigation_id: str,
    payload: InvestigationUpdateRequest,
    db: Session = Depends(get_db),
) -> InvestigationResponse:
    """Update an investigation workspace."""
    updated = InvestigationService.update_investigation(
        db=db, investigation_id=investigation_id, request=payload
    )
    return InvestigationResponse.from_model(updated)


@router.delete(
    "/{investigation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Investigation Workspace",
    description="Remove an investigation workspace and its associated findings links.",
)
def delete_investigation(
    investigation_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Delete an investigation by ID."""
    InvestigationService.delete_investigation(db=db, investigation_id=investigation_id)


@router.post(
    "/synthesize",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Synthesize Investigation Workspace",
    description=(
        "Automatically assemble an investigation workspace by inspecting "
        "scenario validation runs, findings, and pipeline status."
    ),
)
def synthesize_investigation(
    payload: InvestigationSynthesizeRequest,
    db: Session = Depends(get_db),
) -> InvestigationResponse:
    """Synthesize investigation workspace from scenario evidence."""
    investigation = InvestigationService.synthesize_investigation(
        db=db,
        scenario_id=payload.scenario_id,
        title=payload.title,
        finding_id=payload.finding_id,
    )
    return InvestigationResponse.from_model(investigation)
