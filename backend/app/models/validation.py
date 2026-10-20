"""Validation persistence models for rules, execution runs, and findings."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.investigation import Investigation, ReportArtifact
    from app.models.scenario import Scenario


class ValidationRule(Base):
    """Validation rule entity defining a data quality expectation on a dataset."""

    __tablename__ = "validation_rules"
    __table_args__ = (
        Index("idx_rules_scenario", "scenario_id"),
        Index("idx_rules_dataset", "dataset_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(
        String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id: Mapped[str] = mapped_column(
        String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    parameters: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now()
    )

    # Relationships
    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="validation_rules")
    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="validation_rules")
    validation_findings: Mapped[list[ValidationFinding]] = relationship(
        "ValidationFinding", back_populates="rule", cascade="all, delete-orphan"
    )


class ValidationRun(Base):
    """Validation run entity recording a complete execution of rules for a scenario."""

    __tablename__ = "validation_runs"
    __table_args__ = (Index("idx_val_runs_scenario", "scenario_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(
        String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    fixture_version: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    total_checks: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    passed_checks: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    failed_checks: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    warning_checks: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    skipped_checks: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    error_checks: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    execution_duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now()
    )

    # Relationships
    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="validation_runs")
    findings: Mapped[list[ValidationFinding]] = relationship(
        "ValidationFinding", back_populates="run", cascade="all, delete-orphan"
    )
    report_artifacts: Mapped[list[ReportArtifact]] = relationship(
        "ReportArtifact", back_populates="validation_run", cascade="all, delete-orphan"
    )


class ValidationFinding(Base):
    """Granular data quality finding produced by an executed validation rule."""

    __tablename__ = "validation_findings"
    __table_args__ = (
        Index("idx_findings_run", "run_id"),
        Index("idx_findings_rule", "rule_id"),
        Index("idx_findings_dataset", "dataset_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String, ForeignKey("validation_runs.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[str] = mapped_column(
        String, ForeignKey("validation_rules.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id: Mapped[str] = mapped_column(
        String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    rule_category: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    affected_fields: Mapped[str] = mapped_column(Text, nullable=False)
    affected_record_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    total_record_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    execution_duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now()
    )

    # Relationships
    run: Mapped[ValidationRun] = relationship("ValidationRun", back_populates="findings")
    rule: Mapped[ValidationRule] = relationship(
        "ValidationRule", back_populates="validation_findings"
    )
    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="validation_findings")
    investigations: Mapped[list[Investigation]] = relationship(
        "Investigation", back_populates="initial_finding"
    )

