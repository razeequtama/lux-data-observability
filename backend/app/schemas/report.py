"""Pydantic schemas and enums for report generation and artifact management."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReportFormat(StrEnum):
    """Supported export formats for incident reports."""

    JSON = "json"
    HTML = "html"


class ReportGenerateRequest(BaseModel):
    """Payload to generate an immutable incident report package."""

    scenario_id: str = Field(..., description="Target scenario identifier")
    validation_run_id: str | None = Field(
        default=None,
        description="Validation run identifier (uses latest validation run if omitted)",
    )
    investigation_id: str | None = Field(
        default=None,
        description="Existing investigation workspace identifier if available",
    )
    title: str | None = Field(
        default=None,
        description="Optional custom incident report title",
    )
    verified_facts: list[str] = Field(
        default_factory=list,
        description="Verified observable facts from findings or pipeline logs",
    )
    hypotheses: list[str] = Field(
        default_factory=list,
        description="Working hypotheses and root-cause theories",
    )
    action_items: list[str] = Field(
        default_factory=list,
        description="Remediation steps and follow-up action items",
    )


class ReportGenerateResponse(BaseModel):
    """Response returned upon successful report generation."""

    report_id: str = Field(..., description="Unique generated report identifier")
    investigation_id: str = Field(..., description="Associated investigation workspace identifier")
    generated_at: datetime = Field(..., description="Timestamp of report generation")
    json_url: str = Field(..., description="URL endpoint to download JSON format report")
    html_url: str = Field(..., description="URL endpoint to download HTML format report")


class ReportArtifactResponse(BaseModel):
    """Metadata describing a persisted report artifact."""

    id: str = Field(..., description="Unique report artifact identifier")
    investigation_id: str = Field(..., description="Associated investigation identifier")
    scenario_id: str = Field(..., description="Associated scenario identifier")
    validation_run_id: str = Field(..., description="Associated validation run identifier")
    format: str = Field(..., description="Format type: 'json' or 'html'")
    file_path: str = Field(..., description="Storage filesystem path")
    sha256_hash: str = Field(..., description="SHA-256 cryptographic hash of the artifact")
    file_size_bytes: int = Field(..., description="File size in bytes")
    generated_at: datetime = Field(..., description="Timestamp of generation")

    model_config = ConfigDict(from_attributes=True)


class ReportValidationSummary(BaseModel):
    """Summary of validation execution included in the report."""

    run_id: str
    executed_at: str
    total_rules: int
    passed_count: int
    failed_count: int
    warning_count: int
    quality_health: str
    duration_ms: int | None = None


class ReportFindingDetail(BaseModel):
    """Granular detail of an observed validation finding."""

    id: str
    rule_id: str
    rule_name: str
    category: str
    severity: str
    status: str
    dataset_id: str
    message: str
    affected_record_count: int
    total_record_count: int
    sample_keys: list[str] = Field(default_factory=list)
    sample_line_numbers: list[int] = Field(default_factory=list)
    sample_records: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str


class ReportImpactedAsset(BaseModel):
    """Downstream asset impacted by the findings."""

    node_id: str
    node_name: str
    node_type: str
    impact_status: str
    path: list[str] = Field(default_factory=list)


class ReportPipelineSummary(BaseModel):
    """Pipeline execution metadata included in the report."""

    pipeline_name: str
    execution_status: str
    quality_health: str
    start_time: str
    end_time: str
    duration_ms: int
    records_ingested: int
    records_written: int
    error_message: str | None = None


class IncidentReportData(BaseModel):
    """Complete, self-contained incident report content model."""

    report_id: str = Field(..., description="Unique report identifier")
    investigation_id: str = Field(..., description="Associated investigation ID")
    generated_at: str = Field(..., description="ISO 8601 generation timestamp")
    title: str = Field(..., description="Incident investigation title")
    scenario: dict[str, Any] = Field(..., description="Scenario metadata")
    investigation: dict[str, Any] = Field(
        ..., description="Investigation workspace details (facts, hypotheses, actions)"
    )
    validation_summary: ReportValidationSummary = Field(
        ..., description="Data quality validation execution summary"
    )
    findings: list[ReportFindingDetail] = Field(
        default_factory=list, description="Granular quality findings and row evidence"
    )
    impacted_assets: list[ReportImpactedAsset] = Field(
        default_factory=list, description="Downstream assets within the blast radius"
    )
    pipeline_summary: ReportPipelineSummary | None = Field(
        default=None, description="Recent pipeline execution log summary"
    )
    integrity: dict[str, str] = Field(
        default_factory=dict, description="SHA-256 cryptographic integrity hash"
    )

