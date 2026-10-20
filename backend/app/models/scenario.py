"""Scenario persistence model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.investigation import Investigation, ReportArtifact
    from app.models.lineage import LineageEdge, LineageNode
    from app.models.pipeline import FreshnessCheck, PipelineRun
    from app.models.validation import ValidationRule, ValidationRun


class Scenario(Base):
    """Scenario entity defining an observability evaluation environment."""

    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String, nullable=False, default="synthetic", server_default="synthetic"
    )
    is_bundled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    active_fixture_version: Mapped[str] = mapped_column(
        String, nullable=False, default="defective", server_default="defective"
    )
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
    datasets: Mapped[list[Dataset]] = relationship(
        "Dataset", back_populates="scenario", cascade="all, delete-orphan"
    )
    validation_rules: Mapped[list[ValidationRule]] = relationship(
        "ValidationRule", back_populates="scenario", cascade="all, delete-orphan"
    )
    validation_runs: Mapped[list[ValidationRun]] = relationship(
        "ValidationRun", back_populates="scenario", cascade="all, delete-orphan"
    )
    lineage_nodes: Mapped[list[LineageNode]] = relationship(
        "LineageNode", back_populates="scenario", cascade="all, delete-orphan"
    )
    lineage_edges: Mapped[list[LineageEdge]] = relationship(
        "LineageEdge", back_populates="scenario", cascade="all, delete-orphan"
    )
    pipeline_runs: Mapped[list[PipelineRun]] = relationship(
        "PipelineRun", back_populates="scenario", cascade="all, delete-orphan"
    )
    freshness_checks: Mapped[list[FreshnessCheck]] = relationship(
        "FreshnessCheck", back_populates="scenario", cascade="all, delete-orphan"
    )
    investigations: Mapped[list[Investigation]] = relationship(
        "Investigation", back_populates="scenario", cascade="all, delete-orphan"
    )
    report_artifacts: Mapped[list[ReportArtifact]] = relationship(
        "ReportArtifact", back_populates="scenario", cascade="all, delete-orphan"
    )

