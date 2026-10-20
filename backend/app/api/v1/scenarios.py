"""Scenarios API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.scenario import (
    LoadScenarioRequest,
    LoadScenarioResponse,
    ScenarioDetail,
    ScenarioSummary,
)
from app.services.ingestion.loader import ScenarioLoaderService

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get(
    "",
    response_model=list[ScenarioSummary],
    status_code=status.HTTP_200_OK,
    summary="List Scenarios",
    description="Retrieve all available bundled and custom scenarios.",
)
def list_scenarios(db: Session = Depends(get_db)) -> list[ScenarioSummary]:
    """List all available scenarios."""
    return ScenarioLoaderService.list_scenarios(db)


@router.get(
    "/{scenario_id}",
    response_model=ScenarioDetail,
    status_code=status.HTTP_200_OK,
    summary="Get Scenario Details",
    description="Retrieve detailed configuration, datasets, and rules for a scenario.",
)
def get_scenario(scenario_id: str, db: Session = Depends(get_db)) -> ScenarioDetail:
    """Get scenario details by ID."""
    return ScenarioLoaderService.get_scenario_detail(scenario_id, db)


@router.post(
    "/{scenario_id}/load",
    response_model=LoadScenarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Load Scenario Fixtures",
    description=(
        "Load or reset scenario datasets, rules, lineage DAG, and pipeline history into SQLite."
    ),
)
def load_scenario(
    scenario_id: str,
    payload: LoadScenarioRequest | None = None,
    db: Session = Depends(get_db),
) -> LoadScenarioResponse:
    """Load scenario with either defective or corrected fixtures."""
    fixture_version = payload.fixture_version if payload else "defective"
    return ScenarioLoaderService.load_scenario(
        scenario_id=scenario_id,
        fixture_version=fixture_version,
        db=db,
    )
