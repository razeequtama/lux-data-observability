"""Investigation and report artifact persistence models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.scenario import Scenario
    from app.models.validation import ValidationFinding, ValidationRun


class Investigation(Base):
    """Investigation workspace entity combining findings, hypotheses, and action items."""

    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(
        String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="OPEN", server_default="OPEN"
    )
    initial_finding_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("validation_findings.id", ondelete="SET NULL"), nullable=True
    )
    verified_facts: Mapped[str] = mapped_column(Text, nullable=False)
    hypotheses: Mapped[str] = mapped_column(Text, nullable=False)
    action_items: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="investigations")
    initial_finding: Mapped[ValidationFinding | None] = relationship(
        "ValidationFinding", back_populates="investigations"
    )
    reports: Mapped[list[ReportArtifact]] = relationship(
        "ReportArtifact", back_populates="investigation", cascade="all, delete-orphan"
    )


class ReportArtifact(Base):
    """Generated reproducible incident report artifact (JSON or HTML)."""

    __tablename__ = "report_artifacts"
    __table_args__ = (Index("idx_reports_investigation", "investigation_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False
    )
    scenario_id: Mapped[str] = mapped_column(
        String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    validation_run_id: Mapped[str] = mapped_column(
        String, ForeignKey("validation_runs.id", ondelete="CASCADE"), nullable=False
    )
    format: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now()
    )

    # Relationships
    investigation: Mapped[Investigation] = relationship("Investigation", back_populates="reports")
    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="report_artifacts")
    validation_run: Mapped[ValidationRun] = relationship(
        "ValidationRun", back_populates="report_artifacts"
    )

