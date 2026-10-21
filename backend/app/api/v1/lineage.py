"""Lineage API router exposing lineage DAG visualization, node details, and validation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.validation import ValidationFinding, ValidationRun
from app.schemas.impact import AssetImpactStatus
from app.schemas.lineage import (
    GraphValidationSummary,
    LineageGraphResponse,
    LineageNodeDetailResponse,
    LineageNodeSummary,
    LineageValidateRequest,
)
from app.services.impact.analyzer import ImpactAnalysisService
from app.services.lineage.graph import LineageGraph
from app.services.lineage.layout import build_flow_graph

router = APIRouter(prefix="/lineage", tags=["Lineage"])


def _load_scenario_graph(scenario_id: str, db: Session | None = None) -> LineageGraph:
    """Load a LineageGraph instance from the database or scenario files on disk."""
    if db is not None:
        try:
            return LineageGraph.from_db(db, scenario_id=scenario_id)
        except NotFoundError:
            pass
        except Exception:
            pass

    scenario_file = settings.scenarios_dir / scenario_id / "scenario.json"
    if scenario_file.exists():
        return LineageGraph.from_scenario_file(scenario_file, scenario_id=scenario_id)

    raise NotFoundError(
        code="SCENARIO_NOT_FOUND",
        message=(
            f"Lineage graph for scenario '{scenario_id}' was not found in database or filesystem."
        ),
        details={"scenario_id": scenario_id},
    )


def _resolve_quality_health_statuses(
    graph: LineageGraph,
    scenario_id: str,
    db: Session,
) -> dict[str, str]:
    """Dynamically determine data quality health statuses for all nodes in the graph

    based on the latest executed validation run findings.
    """
    stmt = (
        select(ValidationRun)
        .where(ValidationRun.scenario_id == scenario_id)
        .order_by(ValidationRun.executed_at.desc())
    )
    latest_run = db.execute(stmt).scalars().first()

    if not latest_run:
        return {}

    # Query all failed findings for this run
    stmt_findings = select(ValidationFinding).where(
        ValidationFinding.run_id == latest_run.id,
        ValidationFinding.status == "FAILED",
    )
    failed_findings = db.execute(stmt_findings).scalars().all()

    if not failed_findings:
        return {nid: "HEALTHY" for nid in graph.nodes}

    # Gather failed dataset IDs
    failed_datasets: set[str] = {f.dataset_id for f in failed_findings if f.dataset_id}

    # Resolve failed datasets to root node IDs in graph
    failed_root_nodes: set[str] = set()
    for ds_id in failed_datasets:
        for nid in graph.nodes:
            ndata = graph.get_node(nid)
            if ndata.get("dataset_id") == ds_id:
                failed_root_nodes.add(nid)

    # Classify nodes in graph
    classifications = ImpactAnalysisService.classify_graph_nodes(graph, failed_root_nodes)

    status_map: dict[str, str] = {}
    for nid, tier in classifications.items():
        if tier == AssetImpactStatus.CONFIRMED_FAILED:
            status_map[nid] = "CORRUPTED"
        elif tier == AssetImpactStatus.DIRECTLY_AFFECTED:
            status_map[nid] = "CORRUPTED"
        elif tier == AssetImpactStatus.POTENTIALLY_AFFECTED:
            status_map[nid] = "CORRUPTED"
        else:
            status_map[nid] = "HEALTHY"

    return status_map


@router.get(
    "",
    response_model=LineageGraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Lineage Graph",
    description=(
        "Retrieve directed dependency graph nodes and edges formatted for React Flow, "
        "with non-colliding layout positions auto-computed via Dagre layout algorithms."
    ),
)
def get_lineage_graph(
    scenario_id: str = Query(
        default="monday_revenue_mystery",
        description="Target scenario identifier",
    ),
    db: Session = Depends(get_db),
) -> LineageGraphResponse:
    """Retrieve React Flow compatible lineage graph with computed layout positions."""
    graph = _load_scenario_graph(scenario_id, db=db)
    quality_map = _resolve_quality_health_statuses(graph, scenario_id, db=db)

    return build_flow_graph(
        graph=graph,
        scenario_id=scenario_id,
        quality_statuses=quality_map,
    )


@router.get(
    "/nodes/{node_id}",
    response_model=LineageNodeDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Lineage Node Details",
    description="Retrieve node metadata and direct upstream/downstream connections.",
)
def get_lineage_node_details(
    node_id: str,
    scenario_id: str = Query(
        default="monday_revenue_mystery",
        description="Target scenario identifier",
    ),
    db: Session = Depends(get_db),
) -> LineageNodeDetailResponse:
    """Retrieve detailed node metadata and connections by node ID."""
    graph = _load_scenario_graph(scenario_id, db=db)

    if not graph.has_node(node_id):
        raise NotFoundError(
            code="NODE_NOT_FOUND",
            message=f"Lineage node '{node_id}' does not exist in scenario '{scenario_id}'.",
            details={"node_id": node_id, "scenario_id": scenario_id},
        )

    raw_node = graph.get_node(node_id)
    quality_map = _resolve_quality_health_statuses(graph, scenario_id, db=db)

    direct_up_ids = graph.get_direct_upstream(node_id)
    direct_down_ids = graph.get_direct_downstream(node_id)
    total_ancestor_ids = graph.get_upstream_nodes(node_id)
    total_descendant_ids = graph.get_downstream_nodes(node_id)
    upstream_ds_ids = sorted(graph.get_upstream_dataset_ids(node_id))

    def _to_summary(nid: str) -> LineageNodeSummary:
        data = graph.get_node(nid)
        return LineageNodeSummary(
            id=nid,
            name=str(data.get("name", nid)),
            type=str(data.get("type", "DERIVED_DATASET")),
            dataset_id=data.get("dataset_id"),
            execution_status=str(data.get("execution_status") or "COMPLETED_SUCCESS"),
            quality_health=quality_map.get(nid) or str(data.get("quality_health") or "HEALTHY"),
        )

    upstream_summaries = [_to_summary(uid) for uid in direct_up_ids]
    downstream_summaries = [_to_summary(did) for did in direct_down_ids]

    meta = raw_node.get("metadata") or {}
    if isinstance(meta, str):
        meta = {}

    return LineageNodeDetailResponse(
        id=node_id,
        scenario_id=scenario_id,
        name=str(raw_node.get("name", node_id)),
        type=str(raw_node.get("type", "DERIVED_DATASET")),
        dataset_id=raw_node.get("dataset_id"),
        owner=raw_node.get("owner"),
        description=raw_node.get("description"),
        execution_status=str(raw_node.get("execution_status") or "COMPLETED_SUCCESS"),
        quality_health=quality_map.get(node_id) or str(raw_node.get("quality_health") or "HEALTHY"),
        metadata=meta if isinstance(meta, dict) else {},
        upstream_nodes=upstream_summaries,
        downstream_nodes=downstream_summaries,
        direct_upstream_count=len(direct_up_ids),
        direct_downstream_count=len(direct_down_ids),
        total_ancestors_count=len(total_ancestor_ids),
        total_descendants_count=len(total_descendant_ids),
        upstream_dataset_ids=upstream_ds_ids,
    )


@router.post(
    "/validate",
    response_model=GraphValidationSummary,
    status_code=status.HTTP_200_OK,
    summary="Validate Lineage Graph Integrity",
    description=(
        "Validate declared lineage definitions against DAG integrity rules, "
        "detecting cycles, dangling edges, and isolated nodes."
    ),
)
def validate_lineage(
    payload: LineageValidateRequest | None = None,
    db: Session = Depends(get_db),
) -> GraphValidationSummary:
    """Validate declared lineage definitions and return structural integrity report."""
    req = payload or LineageValidateRequest()

    # If explicit nodes and edges are provided, construct and validate an ad-hoc graph
    if req.nodes is not None and len(req.nodes) > 0:
        graph = LineageGraph(
            scenario_id=req.scenario_id,
            name=f"validate_{req.scenario_id or 'adhoc'}",
        )
        for n in req.nodes:
            graph.add_node(n)
        for e in req.edges or []:
            graph.add_edge(
                source=e.source,
                target=e.target,
                edge_id=e.id,
                dependency_type=e.dependency_type,
            )
        return graph.validate_integrity(allow_isolated=req.allow_isolated)

    # Otherwise validate stored graph for scenario_id
    effective_scenario = req.scenario_id or "monday_revenue_mystery"
    graph = _load_scenario_graph(effective_scenario, db=db)
    return graph.validate_integrity(allow_isolated=req.allow_isolated)
