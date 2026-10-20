"""Dataset persistence model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.lineage import LineageNode
    from app.models.pipeline import FreshnessCheck
    from app.models.scenario import Scenario
    from app.models.validation import ValidationFinding, ValidationRule


class Dataset(Base):
    """Dataset entity representing an ingested table or file within a scenario."""

    __tablename__ = "datasets"
    __table_args__ = (Index("idx_datasets_scenario", "scenario_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(
        String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_format: Mapped[str] = mapped_column(String, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    record_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    column_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    schema_definition: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), server_default=func.now()
    )

    # Relationships
    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="datasets")
    validation_rules: Mapped[list[ValidationRule]] = relationship(
        "ValidationRule", back_populates="dataset", cascade="all, delete-orphan"
    )
    validation_findings: Mapped[list[ValidationFinding]] = relationship(
        "ValidationFinding", back_populates="dataset", cascade="all, delete-orphan"
    )
    lineage_nodes: Mapped[list[LineageNode]] = relationship("LineageNode", back_populates="dataset")
    freshness_checks: Mapped[list[FreshnessCheck]] = relationship(
        "FreshnessCheck", back_populates="dataset", cascade="all, delete-orphan"
    )
