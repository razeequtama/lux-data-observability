"""Impact Analysis API router exposing downstream blast radius tracing endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.impact import BlastRadiusReport, ImpactTraceRequest
from app.services.impact.analyzer import ImpactAnalysisService

router = APIRouter(prefix="/impact", tags=["Impact"])


@router.post(
    "/trace",
    response_model=BlastRadiusReport,
    status_code=status.HTTP_200_OK,
    summary="Trace Downstream Impact",
    description=(
        "Trace downstream impact blast radius and affected asset paths originating from "
        "a target failed check, dataset, rule, or lineage node."
    ),
)
def trace_downstream_impact(
    payload: ImpactTraceRequest,
    db: Session = Depends(get_db),
) -> BlastRadiusReport:
    """Calculate downstream blast radius and affected assets from a target entity."""
    return ImpactAnalysisService.trace_impact(
        target_id=payload.target_id,
        target_type=payload.target_type,
        scenario_id=payload.scenario_id,
        include_transformations=payload.include_transformations,
        include_root=payload.include_root,
        db=db,
    )

