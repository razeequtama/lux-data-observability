"""Pydantic schemas for scenarios and scenario loader."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.dataset import DatasetResponse


class ScenarioSummary(BaseModel):
    """Scenario list summary conforming to API contract."""

    id: str = Field(..., description="Scenario identifier")
    name: str = Field(..., description="Human-readable scenario title")
    description: str | None = Field(default=None, description="Detailed problem narrative")
    category: str = Field(default="synthetic", description="Scenario business domain")
    is_bundled: bool = Field(default=True, description="Whether scenario is shipped with platform")
    active_fixture_version: str = Field(
        default="defective", description="Active fixture version: defective or corrected"
    )
    dataset_count: int = Field(default=0, description="Number of declared datasets")
    rule_count: int = Field(default=0, description="Number of declared quality rules")


class ScenarioDetail(BaseModel):
    """Detailed scenario schema including associated datasets."""

    id: str = Field(..., description="Scenario identifier")
    name: str = Field(..., description="Human-readable scenario title")
    description: str | None = Field(default=None, description="Detailed problem narrative")
    category: str = Field(default="synthetic", description="Scenario business domain")
    is_bundled: bool = Field(default=True, description="Whether scenario is shipped with platform")
    active_fixture_version: str = Field(
        default="defective", description="Active fixture version: defective or corrected"
    )
    dataset_count: int = Field(default=0, description="Total datasets")
    rule_count: int = Field(default=0, description="Total quality rules")
    datasets: list[DatasetResponse] = Field(
        default_factory=list, description="Associated dataset objects"
    )
    created_at: datetime | str | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | str | None = Field(default=None, description="Last updated timestamp")


class LoadScenarioRequest(BaseModel):
    """Request payload for loading or resetting scenario fixtures."""

    fixture_version: Literal["defective", "corrected"] = Field(
        default="defective",
        description=(
            "Fixture version to load: 'defective' (initial corrupted state) "
            "or 'corrected' (clean recovery state)"
        ),
    )


class LoadScenarioResponse(BaseModel):
    """Response payload returned when a scenario is successfully loaded into SQLite."""

    scenario_id: str = Field(..., description="Scenario identifier")
    active_fixture_version: str = Field(..., description="Loaded fixture version")
    loaded_datasets: list[str] = Field(..., description="List of loaded dataset IDs")
    rules_registered: int = Field(..., description="Number of validation rules registered in DB")
    lineage_nodes_loaded: int = Field(..., description="Number of lineage DAG nodes loaded into DB")
    message: str = Field(..., description="Human-readable status summary")


class UnloadScenarioResponse(BaseModel):
    """Response payload returned when a scenario is successfully unloaded from SQLite."""

    scenario_id: str = Field(..., description="Scenario identifier")
    unloaded_datasets: list[str] = Field(..., description="List of unloaded dataset IDs")
    records_cleared: int = Field(..., description="Total count of dataset records removed")
    message: str = Field(..., description="Human-readable status summary")
