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


class NodePosition(BaseModel):
    """Layout position coordinates formatted for React Flow visualizer."""

    x: float = Field(..., description="Horizontal coordinate in pixels")
    y: float = Field(..., description="Vertical coordinate in pixels")


class ReactFlowNode(BaseModel):
    """React Flow compatible node payload with layout position and dual-dimension statuses."""

    id: str = Field(..., description="Unique node identifier (e.g. 'src_orders')")
    name: str = Field(..., description="Human-readable node label or file name")
    type: str = Field(..., description="Lineage asset classification type")
    dataset_id: str | None = Field(default=None, description="Optional associated dataset ID")
    execution_status: str | None = Field(
        default="COMPLETED_SUCCESS", description="Pipeline execution dimension status"
    )
    quality_health: str | None = Field(
        default="HEALTHY", description="Data quality dimension status"
    )
    position: NodePosition = Field(..., description="Dagre-calculated coordinate position")
    owner: str | None = Field(default=None, description="Asset owner")
    description: str | None = Field(default=None, description="Detailed narrative of asset purpose")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary engine or transformation metadata"
    )
    data: dict[str, Any] = Field(
        default_factory=dict, description="Standard React Flow node data payload"
    )


class ReactFlowEdge(BaseModel):
    """React Flow compatible directional edge linking upstream source to downstream target."""

    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node identifier")
    target: str = Field(..., description="Target node identifier")
    dependency_type: str = Field(default="DIRECT_INPUT", description="Dependency classification")
    animated: bool = Field(
        default=False, description="Whether edge animation is enabled in visualizer"
    )


class LineageGraphResponse(BaseModel):
    """Complete lineage graph payload formatted for React Flow visualizer."""

    scenario_id: str = Field(..., description="Scenario identifier to which this graph belongs")
    nodes: list[ReactFlowNode] = Field(default_factory=list, description="React Flow nodes")
    edges: list[ReactFlowEdge] = Field(default_factory=list, description="React Flow edges")


class LineageNodeSummary(BaseModel):
    """Lightweight node summary for direct upstream and downstream connections."""

    id: str = Field(..., description="Unique node identifier")
    name: str = Field(..., description="Human-readable node label")
    type: str = Field(..., description="Node asset classification type")
    dataset_id: str | None = Field(default=None, description="Associated dataset ID")
    execution_status: str | None = Field(default=None, description="Execution status")
    quality_health: str | None = Field(default=None, description="Quality health")


class LineageNodeDetailResponse(BaseModel):
    """Detailed metadata and direct upstream/downstream connections for a single lineage node."""

    id: str = Field(..., description="Unique node identifier")
    scenario_id: str = Field(..., description="Scenario identifier")
    name: str = Field(..., description="Human-readable node label")
    type: str = Field(..., description="Node asset classification type")
    dataset_id: str | None = Field(default=None, description="Associated dataset ID")
    owner: str | None = Field(default=None, description="Team or engineer responsible for asset")
    description: str | None = Field(default=None, description="Asset description")
    execution_status: str | None = Field(default=None, description="Pipeline execution status")
    quality_health: str | None = Field(default=None, description="Data quality health status")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary node metadata")
    upstream_nodes: list[LineageNodeSummary] = Field(
        default_factory=list, description="Direct upstream predecessor nodes"
    )
    downstream_nodes: list[LineageNodeSummary] = Field(
        default_factory=list, description="Direct downstream successor nodes"
    )
    direct_upstream_count: int = Field(default=0, description="Count of immediate predecessors")
    direct_downstream_count: int = Field(default=0, description="Count of immediate successors")
    total_ancestors_count: int = Field(
        default=0, description="Total count of all upstream ancestors"
    )
    total_descendants_count: int = Field(
        default=0, description="Total count of all downstream descendants"
    )
    upstream_dataset_ids: list[str] = Field(
        default_factory=list, description="Root storage dataset IDs feeding into this asset"
    )


class LineageValidateRequest(BaseModel):
    """Request payload for validating declared lineage definitions."""

    scenario_id: str | None = Field(
        default=None,
        description="Scenario identifier to validate from metadata if nodes/edges omitted",
    )
    nodes: list[LineageNode] | None = Field(
        default=None, description="Optional custom list of nodes to validate"
    )
    edges: list[LineageEdge] | None = Field(
        default=None, description="Optional custom list of edges to validate"
    )
    allow_isolated: bool = Field(
        default=True,
        description="Whether isolated nodes are treated as warnings (True) or fatal errors (False)",
    )
