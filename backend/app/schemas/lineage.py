"""Pydantic schemas for lineage graph nodes, edges, and validation."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class LineageNodeType(StrEnum):
    """Lineage node classification types matching data model specifications."""

    SOURCE_DATASET = "SOURCE_DATASET"
    TRANSFORMATION = "TRANSFORMATION"
    DERIVED_DATASET = "DERIVED_DATASET"
    METRIC = "METRIC"
    REPORT = "REPORT"


class LineageNode(BaseModel):
    """Pydantic model representing a lineage DAG node."""

    id: str = Field(..., description="Unique node identifier (e.g., 'src_orders')")
    name: str = Field(..., description="Human-readable node label or file name")
    type: LineageNodeType | str = Field(..., description="Asset classification type")
    dataset_id: str | None = Field(
        default=None, description="Optional foreign key to associated dataset"
    )
    owner: str | None = Field(default=None, description="Team or engineer responsible for asset")
    description: str | None = Field(default=None, description="Detailed narrative of asset purpose")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary engine or transformation metadata"
    )
    execution_status: str | None = Field(
        default=None, description="Pipeline execution status (e.g. COMPLETED_SUCCESS, FAILED)"
    )
    quality_health: str | None = Field(
        default=None, description="Data quality health status (e.g. HEALTHY, CORRUPTED)"
    )


class LineageEdge(BaseModel):
    """Pydantic model representing a directional dependency edge from source to target."""

    id: str | None = Field(default=None, description="Optional unique edge identifier")
    source: str = Field(..., description="Source node ID (upstream dependency)")
    target: str = Field(..., description="Target node ID (downstream consumer)")
    dependency_type: str = Field(
        default="DIRECT_INPUT", description="Type of dependency link (e.g. DIRECT_INPUT, DERIVED)"
    )


class LineageGraphSchema(BaseModel):
    """Pydantic schema representing complete lineage graph structure."""

    scenario_id: str | None = Field(
        default=None, description="Scenario ID to which this graph belongs"
    )
    nodes: list[LineageNode] = Field(default_factory=list, description="List of lineage nodes")
    edges: list[LineageEdge] = Field(default_factory=list, description="List of lineage edges")


class GraphValidationSummary(BaseModel):
    """Summary of graph integrity validation results."""

    is_valid: bool = Field(..., description="Whether the graph satisfies all DAG integrity checks")
    node_count: int = Field(default=0, description="Total nodes in graph")
    edge_count: int = Field(default=0, description="Total edges in graph")
    is_dag: bool = Field(default=True, description="Whether graph is acyclic (contains no cycles)")
    cycles: list[list[str]] = Field(
        default_factory=list, description="List of detected dependency cycles"
    )
    dangling_edges: list[dict[str, str]] = Field(
        default_factory=list, description="List of edges referencing missing nodes"
    )
    isolated_nodes: list[str] = Field(
        default_factory=list, description="List of disconnected nodes with no edges"
    )
    errors: list[str] = Field(
        default_factory=list, description="Integrity error messages if invalid"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Non-fatal warnings (e.g. isolated nodes)"
    )
