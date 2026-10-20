"""Pipeline persistence models for execution runs and dataset freshness checks."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.scenario import Scenario


class PipelineRun(Base):
    """Pipeline run entity tracking compute execution status and data quality dimensions."""

    __tablename__ = "pipeline_runs"
    __table_args__ = (Index("idx_pipeline_runs_scenario", "scenario_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(
        String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    pipeline_name: Mapped[str] = mapped_column(String, nullable=False)
    execution_status: Mapped[str] = mapped_column(String, nullable=False)
    quality_health: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    records_ingested: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    records_written: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now()
    )

    # Relationships
    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="pipeline_runs")


class FreshnessCheck(Base):
    """Dataset partition freshness checkpoint tracking SLA expectations."""

    __tablename__ = "freshness_checks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(
        String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id: Mapped[str] = mapped_column(
        String, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    expected_partition_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    observed_partition_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sla_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now()
    )

    # Relationships
    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="freshness_checks")
    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="freshness_checks")
