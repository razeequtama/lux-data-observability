"""Pydantic schemas and enums for validation rules, configurations, and evaluation results."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


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
