"""Reports API router for incident report generation and export downloads."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.investigation import ReportArtifact
from app.schemas.report import (
    ReportArtifactResponse,
    ReportGenerateRequest,
    ReportGenerateResponse,
)
from app.services.reports.generator import ReportGeneratorService

router = APIRouter(prefix="/reports", tags=["Reports"])

CSP_HEADER_VALUE = "default-src 'none'; style-src 'unsafe-inline'; img-src data:; sandbox;"


@router.post(
    "/generate",
    response_model=ReportGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Incident Report",
    description=(
        "Generate reproducible, immutable JSON and safe styled HTML incident reports "
        "backed by concrete validation findings and downstream impact analysis."
    ),
)
def generate_report(
    payload: ReportGenerateRequest,
    db: Session = Depends(get_db),
) -> ReportGenerateResponse:
    """Generate and persist an incident report package."""
    return ReportGeneratorService.generate_report(db=db, request=payload)


@router.get(
    "/{report_id}/export",
    status_code=status.HTTP_200_OK,
    summary="Download Report Artifact",
    description=(
        "Download generated report artifact in JSON or HTML format with "
        "Content Security Policy headers."
    ),
    responses={
        200: {
            "content": {
                "application/json": {},
                "text/html": {},
            },
            "description": "Exported report file content.",
        }
    },
)
def export_report_artifact(
    report_id: str,
    export_format: str = Query(
        "json", alias="format", description="Export format: 'json' or 'html'"
    ),
    db: Session = Depends(get_db),
) -> Response:
    """Export and stream report artifact."""
    artifact, file_path = ReportGeneratorService.get_report_artifact(
        db=db, report_id=report_id, export_format=export_format
    )

    content = file_path.read_text(encoding="utf-8")

    if artifact.format == "html":
        return Response(
            content=content,
            media_type="text/html; charset=utf-8",
            headers={
                "Content-Security-Policy": CSP_HEADER_VALUE,
                "Content-Disposition": f'inline; filename="{report_id}.html"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'inline; filename="{report_id}.json"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get(
    "/{report_id}",
    response_model=list[ReportArtifactResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Report Artifacts by ID",
    description="Retrieve artifact records associated with a report or investigation ID.",
)
def get_report_artifacts(
    report_id: str,
    db: Session = Depends(get_db),
) -> list[ReportArtifactResponse]:
    """Retrieve artifacts associated with a report or investigation."""
    artifacts, _ = ReportGeneratorService.list_artifacts(
        db=db, investigation_id=report_id, limit=50, offset=0
    )
    if not artifacts:
        # Also check by report ID prefix
        direct_matches = list(
            db.scalars(
                select(ReportArtifact).where(
                    (ReportArtifact.id == f"{report_id}_json")
                    | (ReportArtifact.id == f"{report_id}_html")
                    | (ReportArtifact.id == report_id)
                )
            ).all()
        )
        artifacts = direct_matches

    return [ReportArtifactResponse.model_validate(a) for a in artifacts]


@router.get(
    "",
    response_model=list[ReportArtifactResponse],
    status_code=status.HTTP_200_OK,
    summary="List Report Artifacts",
    description="List generated report artifacts with optional scenario and investigation filters.",
)
def list_report_artifacts(
    scenario_id: str | None = Query(None, description="Filter by scenario ID"),
    investigation_id: str | None = Query(None, description="Filter by investigation ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
) -> list[ReportArtifactResponse]:
    """List persisted report artifacts."""
    artifacts, _ = ReportGeneratorService.list_artifacts(
        db=db,
        scenario_id=scenario_id,
        investigation_id=investigation_id,
        limit=limit,
        offset=offset,
    )
    return [ReportArtifactResponse.model_validate(a) for a in artifacts]
