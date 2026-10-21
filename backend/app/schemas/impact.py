"""Pydantic schemas for downstream impact analysis and blast radius classification."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AssetImpactStatus(StrEnum):
    """Impact classification tiers conforming to data model specification and ADR-006."""

    CONFIRMED_FAILED = "CONFIRMED_FAILED"
    DIRECTLY_AFFECTED = "DIRECTLY_AFFECTED"
    POTENTIALLY_AFFECTED = "POTENTIALLY_AFFECTED"
    HEALTHY = "HEALTHY"


class ImpactTargetType(StrEnum):
    """Supported target entity types for impact analysis queries."""

    FINDING = "FINDING"
    DATASET = "DATASET"
    NODE = "NODE"
    RULE = "RULE"
    AUTO = "AUTO"


class AffectedAsset(BaseModel):
    """Represents a single downstream asset impacted by an upstream defect or failure."""

    node_id: str = Field(..., description="Unique lineage node identifier (e.g. 'dim_orders')")
    name: str = Field(..., description="Human-readable asset label or file name")
    type: str = Field(..., description="Lineage asset type (e.g. DERIVED_DATASET, METRIC, REPORT)")
    impact_status: AssetImpactStatus = Field(
        ...,
        description="Impact tier (CONFIRMED_FAILED, DIRECTLY_AFFECTED, POTENTIALLY_AFFECTED)",
    )
    distance: int = Field(
        ...,
        description="Shortest graph distance (hops) from the root failed entity",
    )
    dependency_path: list[str] = Field(
        ...,
        description="Node ID sequence connecting root entity to this asset",
    )
    dependency_path_names: list[str] = Field(
        default_factory=list,
        description="Human-readable asset name sequence connecting root entity to this asset",
    )
    explanation: str | None = Field(
        default=None, description="Human-readable dependency path explanation string"
    )


class ImpactSummary(BaseModel):
    """Summary counts of impacted assets grouped by classification tier."""

    confirmed_failed: int = Field(
        default=0, description="Total count of assets that directly produced validation failures"
    )
    directly_affected: int = Field(
        default=0, description="Total count of immediate downstream consumers of corrupted data"
    )
    potentially_affected: int = Field(
        default=0, description="Total count of transitive downstream consumers in dependency paths"
    )
    healthy: int = Field(
        default=0, description="Total count of unaffected assets in the examined scope"
    )


class ImpactTraceRequest(BaseModel):
    """Request payload for downstream impact tracing."""

    scenario_id: str = Field(
        default="monday_revenue_mystery", description="Target scenario identifier"
    )
    target_type: ImpactTargetType | str = Field(
        default=ImpactTargetType.AUTO,
        description="Type of target entity: 'FINDING', 'DATASET', 'NODE', 'RULE', or 'AUTO'",
    )
    target_id: str = Field(
        ...,
        description="Target ID (e.g. 'VAL-ORD-001', 'orders.csv', 'orders', 'src_orders')",
    )
    include_transformations: bool = Field(
        default=False,
        description="Whether to include intermediate transformations in affected assets list",
    )
    include_root: bool = True


class BlastRadiusReport(BaseModel):
    """Comprehensive blast radius evaluation report returned by downstream impact analysis."""

    target_id: str = Field(..., description="Queried target entity identifier")
    target_type: str = Field(default="DATASET", description="Resolved or queried target type")
    root_node_id: str = Field(
        ..., description="Root lineage node ID where failure or defect originates"
    )
    root_dataset_id: str | None = Field(
        default=None, description="Dataset ID associated with the root node, if applicable"
    )
    scenario_id: str | None = Field(
        default=None, description="Scenario ID associated with the lineage graph"
    )
    total_affected_assets: int = Field(
        ..., description="Total count of affected assets in this blast radius"
    )
    impact_summary: ImpactSummary = Field(
        ..., description="Summary breakdown of affected assets by tier"
    )
    affected_assets: list[AffectedAsset] = Field(
        default_factory=list, description="Ordered list of affected assets sorted by distance"
    )
