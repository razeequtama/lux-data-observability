"""Recovery verification API router exposing endpoints to verify scenario recovery."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.recovery import RecoveryVerifyRequest, RecoveryVerifyResponse
from app.services.validation.recovery import RecoveryService

router = APIRouter(prefix="/recovery", tags=["Recovery"])


@router.post(
    "/verify",
    response_model=RecoveryVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Scenario Recovery",
    description=(
        "Swap scenario dataset fixtures to corrected version, re-execute validation rules, "
        "compute before-and-after resolution diffs, and verify downstream asset health recovery."
    ),
)
def verify_recovery(
    payload: RecoveryVerifyRequest,
    db: Session = Depends(get_db),
) -> RecoveryVerifyResponse:
    """Verify recovery by executing validation against clean fixtures and calculating diff."""
    return RecoveryService.verify_recovery(
        scenario_id=payload.scenario_id,
        db=db,
        target_fixture_version=payload.target_fixture_version,
    )
