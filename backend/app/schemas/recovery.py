"""Pydantic schemas for recovery verification and before-and-after diff comparisons."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RecoveryRunSummary(BaseModel):
    """Summary of a validation run participating in a recovery comparison."""

    run_id: str = Field(..., description="Unique validation run identifier")
    fixture_version: str = Field(
        ..., description="Fixture version used for run ('defective' or 'corrected')"
    )
    failed_checks: int = Field(..., description="Total count of failed validation checks")
    quality_health: str = Field(..., description="Overall data quality health status")
    total_checks: int | None = Field(
        default=None, description="Total count of checks evaluated in this run"
    )
    passed_checks: int | None = Field(
        default=None, description="Total count of checks that passed in this run"
    )
    execution_duration_ms: int | None = Field(
        default=None, description="Execution duration in milliseconds"
    )
    executed_at: datetime | None = Field(
        default=None, description="Timestamp when validation run was executed"
    )


class ResolvedFindingItem(BaseModel):
    """Individual data quality finding evaluated across before-and-after runs."""

    rule_id: str = Field(..., description="Validation rule identifier")
    rule_name: str = Field(..., description="Human-readable rule name")
    status: str = Field(
        ...,
        description=(
            "Resolution status: 'RESOLVED' if passing after recovery, 'UNRESOLVED' otherwise"
        ),
    )
    severity: str | None = Field(
        default=None, description="Severity of the original validation rule"
    )
    category: str | None = Field(
        default=None, description="Rule category (e.g. UNIQUENESS, VALUE_RANGE)"
    )
    dataset_id: str | None = Field(default=None, description="Associated dataset identifier")
    previous_status: str | None = Field(
        default=None, description="Validation status in previous run (e.g. FAILED)"
    )
    current_status: str | None = Field(
        default=None, description="Validation status in current run (e.g. PASSED)"
    )
    message: str | None = Field(default=None, description="Diagnostic message or resolution note")


class RecoveryComparison(BaseModel):
    """Detailed comparison between baseline defective run and current recovery run."""

    previous_run: RecoveryRunSummary = Field(
        ..., description="Baseline previous validation run before recovery"
    )
    current_run: RecoveryRunSummary = Field(
        ..., description="Validation run executed after applying recovery fixtures"
    )
    resolved_findings: list[ResolvedFindingItem] = Field(
        ..., description="List of findings evaluated for resolution"
    )
    downstream_recovery_status: str = Field(
        ...,
        description=(
            "Overall recovery status of downstream assets "
            "('ALL_ASSETS_HEALTHY', 'PARTIALLY_RECOVERED', 'RECOVERY_FAILED')"
        ),
    )


class RecoveryVerifyRequest(BaseModel):
    """Payload to trigger recovery verification for a scenario."""

    scenario_id: str = Field(..., description="Scenario identifier to verify recovery for")
    target_fixture_version: str = Field(
        default="corrected",
        description="Target fixture version to verify recovery with (defaults to 'corrected')",
    )


class RecoveryVerifyResponse(BaseModel):
    """Envelope response returned after executing recovery verification."""

    scenario_id: str = Field(..., description="Scenario identifier")
    comparison: RecoveryComparison = Field(
        ..., description="Detailed recovery before-and-after comparison"
    )
