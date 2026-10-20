"""Lineage persistence models for DAG nodes and dependency edges."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.scenario import Scenario


class LineageNode(Base):
    """Lineage node representing a dataset, transformation, metric, or report in the DAG."""

    __tablename__ = "lineage_nodes"
    __table_args__ = (Index("idx_nodes_scenario", "scenario_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(
        String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    node_type: Mapped[str] = mapped_column(String, nullable=False)
    dataset_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True
    )
    owner: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Mapped to DB column 'metadata'. Python attribute is node_metadata to avoid
    # colliding with DeclarativeBase.metadata.
    node_metadata: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)

    # Relationships
    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="lineage_nodes")
    dataset: Mapped[Dataset | None] = relationship("Dataset", back_populates="lineage_nodes")
    outgoing_edges: Mapped[list[LineageEdge]] = relationship(
        "LineageEdge",
        foreign_keys="[LineageEdge.source_id]",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )
    incoming_edges: Mapped[list[LineageEdge]] = relationship(
        "LineageEdge",
        foreign_keys="[LineageEdge.target_id]",
        back_populates="target_node",
        cascade="all, delete-orphan",
    )


class LineageEdge(Base):
    """Lineage edge representing a directional dependency from source node to target node."""

    __tablename__ = "lineage_edges"
    __table_args__ = (
        Index("idx_edges_scenario", "scenario_id"),
        Index("idx_edges_source", "source_id"),
        Index("idx_edges_target", "target_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(
        String, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[str] = mapped_column(
        String, ForeignKey("lineage_nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[str] = mapped_column(
        String, ForeignKey("lineage_nodes.id", ondelete="CASCADE"), nullable=False
    )
    dependency_type: Mapped[str] = mapped_column(
        String, nullable=False, default="DIRECT_INPUT", server_default="DIRECT_INPUT"
    )

    # Relationships
    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="lineage_edges")
    source_node: Mapped[LineageNode] = relationship(
        "LineageNode", foreign_keys=[source_id], back_populates="outgoing_edges"
    )
    target_node: Mapped[LineageNode] = relationship(
        "LineageNode", foreign_keys=[target_id], back_populates="incoming_edges"
    )
