"""Pydantic schemas and enums for validation rules, configurations, and evaluation results."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuleCategory(StrEnum):
    """Data quality rule categories supported by the validation engine."""

    NULL_CHECK = "NULL_CHECK"
    UNIQUENESS = "UNIQUENESS"
    TYPE_VALIDITY = "TYPE_VALIDITY"
    RECORD_COUNT = "RECORD_COUNT"
    VALUE_RANGE = "VALUE_RANGE"
    REFERENTIAL_INTEGRITY = "REFERENTIAL_INTEGRITY"
    TEMPORAL_ANOMALY = "TEMPORAL_ANOMALY"
    SCHEMA_INTEGRITY = "SCHEMA_INTEGRITY"
    FRESHNESS = "FRESHNESS"


class RuleSeverity(StrEnum):
    """Severity levels for validation rules and findings."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class RuleStatus(StrEnum):
    """Execution status for a validation check."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class ValidationRuleConfig(BaseModel):
    """Declarative validation rule specification."""

    id: str = Field(..., description="Unique rule identifier (e.g. VAL-ORD-001)")
    dataset_id: str = Field(..., description="Target dataset ID")
    name: str = Field(..., description="Human-readable rule name")
    category: RuleCategory | str = Field(..., description="Validation rule category")
    severity: RuleSeverity | str = Field(
        default=RuleSeverity.HIGH, description="Rule failure severity"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Rule-specific configuration parameters"
    )
    description: str = Field(default="", description="Description of the rule expectation")
    is_active: bool = Field(default=True, description="Whether this rule is active for execution")


class RuleEvaluationResult(BaseModel):
    """Structured result returned by a rule evaluator."""

    rule_id: str = Field(..., description="Executed rule identifier")
    rule_name: str = Field(..., description="Executed rule name")
    rule_category: RuleCategory | str = Field(..., description="Rule category")
    severity: RuleSeverity | str = Field(..., description="Severity level")
    status: RuleStatus | str = Field(
        ..., description="Outcome status (PASSED, FAILED, WARNING, ERROR)"
    )
    dataset_id: str = Field(..., description="Target dataset identifier")
    affected_fields: list[str] = Field(
        default_factory=list, description="Fields evaluated or violating expectation"
    )
    affected_record_count: int = Field(default=0, description="Count of violating records")
    total_record_count: int = Field(default=0, description="Total records evaluated in the dataset")
    message: str = Field(..., description="Human-readable outcome explanation")
    evidence: dict[str, Any] = Field(
        default_factory=dict, description="Structured diagnostics and sample row keys"
    )
    execution_duration_ms: int = Field(
        default=0, description="Evaluation execution duration in milliseconds"
    )


class ValidationRunRequest(BaseModel):
    """Payload to initiate a validation run for a scenario."""

    scenario_id: str = Field(..., description="Target scenario identifier to validate")
    dataset_ids: list[str] | None = Field(
        default=None,
        description="Optional list of dataset IDs. If omitted, all datasets are validated.",
    )


class ValidationRunResponse(BaseModel):
    """Execution summary of a completed validation run."""

    run_id: str = Field(..., description="Unique validation run identifier")
    scenario_id: str = Field(..., description="Scenario identifier")
    fixture_version: str = Field(
        ..., description="Active fixture version evaluated ('defective' or 'corrected')"
    )
    status: str = Field(
        ..., description="Overall run outcome status ('PASSED', 'FAILED', 'WARNING')"
    )
    total_checks: int = Field(default=0, description="Total validation checks executed")
    passed_checks: int = Field(default=0, description="Count of checks that passed")
    failed_checks: int = Field(default=0, description="Count of checks that failed")
    warning_checks: int = Field(default=0, description="Count of warning checks")
    skipped_checks: int = Field(default=0, description="Count of skipped checks")
    error_checks: int = Field(default=0, description="Count of error checks")
    execution_duration_ms: int = Field(
        default=0, description="Total execution duration in milliseconds"
    )
    executed_at: datetime = Field(..., description="Timestamp when validation run completed")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, run: Any) -> ValidationRunResponse:
        """Construct response schema from SQLAlchemy ValidationRun model."""
        return cls(
            run_id=getattr(run, "id", getattr(run, "run_id", "")),
            scenario_id=run.scenario_id,
            fixture_version=run.fixture_version,
            status=run.status,
            total_checks=run.total_checks,
            passed_checks=run.passed_checks,
            failed_checks=run.failed_checks,
            warning_checks=run.warning_checks,
            skipped_checks=run.skipped_checks,
            error_checks=run.error_checks,
            execution_duration_ms=run.execution_duration_ms,
            executed_at=run.executed_at,
        )


class ValidationFindingItem(BaseModel):
    """Structured granular data quality finding for an executed check."""

    id: str = Field(..., description="Unique finding identifier")
    rule_id: str = Field(..., description="Executed rule identifier")
    rule_name: str = Field(..., description="Human-readable rule name")
    rule_category: str = Field(..., description="Validation rule category")
    severity: str = Field(..., description="Rule severity level")
    status: str = Field(..., description="Outcome status ('PASSED', 'FAILED', 'WARNING', etc.)")
    dataset_id: str = Field(..., description="Target dataset identifier")
    affected_fields: list[str] = Field(
        default_factory=list, description="Fields evaluated or violating expectation"
    )
    affected_record_count: int = Field(default=0, description="Count of violating records")
    total_record_count: int = Field(default=0, description="Total records evaluated in the dataset")
    message: str = Field(..., description="Human-readable outcome explanation")
    evidence: dict[str, Any] = Field(
        default_factory=dict, description="Structured diagnostics and sample row keys"
    )
    execution_duration_ms: int = Field(
        default=0, description="Evaluation execution duration in milliseconds"
    )
    created_at: datetime | None = Field(
        default=None, description="Timestamp when finding was recorded"
    )

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, finding: Any) -> ValidationFindingItem:
        """Construct schema from SQLAlchemy ValidationFinding model."""
        affected_fields = finding.affected_fields
        if isinstance(affected_fields, str):
            try:
                affected_fields = json.loads(affected_fields)
            except (json.JSONDecodeError, TypeError):
                affected_fields = []

        evidence = finding.evidence
        if isinstance(evidence, str):
            try:
                evidence = json.loads(evidence)
            except (json.JSONDecodeError, TypeError):
                evidence = {}

        rule_name = (
            finding.rule.name if getattr(finding, "rule", None) else getattr(finding, "rule_id", "")
        )

        return cls(
            id=finding.id,
            rule_id=finding.rule_id,
            rule_name=rule_name,
            rule_category=finding.rule_category,
            severity=finding.severity,
            status=finding.status,
            dataset_id=finding.dataset_id,
            affected_fields=affected_fields or [],
            affected_record_count=finding.affected_record_count,
            total_record_count=finding.total_record_count,
            message=finding.message,
            evidence=evidence or {},
            execution_duration_ms=finding.execution_duration_ms,
            created_at=getattr(finding, "created_at", None),
        )


class ValidationFindingsListResponse(BaseModel):
    """Paginated list response of validation findings."""

    run_id: str = Field(..., description="Associated validation run identifier")
    total_findings: int = Field(
        ..., description="Total count of findings matching the query filter"
    )
    items: list[ValidationFindingItem] = Field(
        default_factory=list, description="List of finding items"
    )


class ValidationRunListResponse(BaseModel):
    """List response of validation runs."""

    total: int = Field(..., description="Total count of validation runs")
    items: list[ValidationRunResponse] = Field(
        default_factory=list, description="List of validation runs"
    )
