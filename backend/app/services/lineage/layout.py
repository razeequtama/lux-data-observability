"""Dagre layout engine and React Flow graph formatting service for lineage DAGs."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import networkx as nx

from app.schemas.lineage import (
    LineageGraphResponse,
    NodePosition,
    ReactFlowEdge,
    ReactFlowNode,
)
from app.services.lineage.graph import LineageGraph


def compute_dagre_layout(
    graph: LineageGraph,
    margin_x: float = 50.0,
    margin_y: float = 100.0,
    rank_sep: float = 230.0,
    node_sep: float = 100.0,
) -> dict[str, dict[str, float]]:
    """Compute non-colliding (x, y) coordinates for lineage graph nodes using Sugiyama/Dagre layout.

    Arranges nodes in a directed left-to-right (LR) topological hierarchy:
    1. Assigns each node to a layer/rank via longest-path distance from roots.
    2. Orders nodes within each rank using the barycenter heuristic to minimize edge crossings.
    3. Positions nodes horizontally by rank (x = margin_x + rank * rank_sep).
    4. Positions nodes vertically within each rank, enforcing minimum node_sep spacing.

    Args:
        graph: LineageGraph domain instance.
        margin_x: Initial horizontal margin (X position of rank 0 nodes).
        margin_y: Initial vertical margin (Y position of uppermost node).
        rank_sep: Horizontal distance between consecutive ranks/layers.
        node_sep: Minimum vertical separation between nodes in the same rank.

    Returns:
        Mapping of node_id -> {"x": float, "y": float}.
    """
    g = graph._graph
    if g.number_of_nodes() == 0:
        return {}

    # Fallback for cyclic graphs: compute spring layout with valid positive coordinates
    if not nx.is_directed_acyclic_graph(g):
        spring_pos = nx.spring_layout(g, seed=42)
        fallback_positions: dict[str, dict[str, float]] = {}
        for nid, coords in spring_pos.items():
            fallback_positions[nid] = {
                "x": round(float(coords[0] * 500.0 + 300.0), 1),
                "y": round(float(coords[1] * 300.0 + 200.0), 1),
            }
        return fallback_positions

    # 1. Rank Assignment (Longest-path layering in topological order)
    ranks: dict[str, int] = {}
    for n in nx.topological_sort(g):
        preds = list(g.predecessors(n))
        ranks[n] = 0 if not preds else max(ranks[p] + 1 for p in preds)

    layers: dict[int, list[str]] = defaultdict(list)
    for n, r in ranks.items():
        layers[r].append(n)

    positions: dict[str, dict[str, float]] = {}

    # 2. Layer 0 Placement
    layer_0_nodes = sorted(
        layers[0],
        key=lambda nid: (
            # Keep dataset nodes grouped if metadata present, else deterministic node_id
            str(graph.get_node(nid).get("type", "")),
            nid,
        ),
    )
    for idx, nid in enumerate(layer_0_nodes):
        positions[nid] = {
            "x": round(margin_x, 1),
            "y": round(margin_y + idx * node_sep, 1),
        }

    # 3. Subsequent Layers Placement using Predecessor Barycenter
    max_rank = max(layers.keys()) if layers else 0
    for r in range(1, max_rank + 1):
        layer_nodes = layers[r]

        def get_barycenter(nid: str) -> float:
            preds = list(g.predecessors(nid))
            if not preds:
                return margin_y
            return sum(positions[p]["y"] for p in preds if p in positions) / len(preds)

        # Sort layer nodes by predecessor barycenter to untangle crossings
        layer_nodes.sort(key=lambda nid: (get_barycenter(nid), nid))
        x = margin_x + r * rank_sep

        # Calculate ideal y positions centered on predecessor barycenters
        assigned_y: list[float] = []
        for nid in layer_nodes:
            preds = list(g.predecessors(nid))
            if preds:
                ideal_y = sum(positions[p]["y"] for p in preds if p in positions) / len(preds)
            else:
                ideal_y = margin_y
            assigned_y.append(ideal_y)

        # Enforce minimum node_sep separation between consecutive nodes in the layer
        for i in range(1, len(assigned_y)):
            if assigned_y[i] < assigned_y[i - 1] + node_sep:
                assigned_y[i] = assigned_y[i - 1] + node_sep

        for nid, y in zip(layer_nodes, assigned_y, strict=False):
            positions[nid] = {
                "x": round(x, 1),
                "y": round(y, 1),
            }

    return positions


def build_flow_graph(
    graph: LineageGraph,
    scenario_id: str | None = None,
    quality_statuses: dict[str, str] | None = None,
    execution_statuses: dict[str, str] | None = None,
) -> LineageGraphResponse:
    """Format a LineageGraph into a React Flow compatible response payload.

    Args:
        graph: LineageGraph domain instance.
        scenario_id: Target scenario identifier.
        quality_statuses: Optional mapping of node_id -> quality_health status string.
        execution_statuses: Optional mapping of node_id -> execution_status string.

    Returns:
        LineageGraphResponse conforming to REST API contracts.
    """
    effective_scenario = scenario_id or graph.scenario_id or "monday_revenue_mystery"
    positions = compute_dagre_layout(graph)

    q_map = quality_statuses or {}
    e_map = execution_statuses or {}

    react_nodes: list[ReactFlowNode] = []
    for nid in graph.nodes:
        raw_data = graph.get_node(nid)
        pos = positions.get(nid, {"x": 50.0, "y": 100.0})

        name = str(raw_data.get("name", nid))
        node_type = str(raw_data.get("type", "DERIVED_DATASET"))
        dataset_id = raw_data.get("dataset_id")
        owner = raw_data.get("owner")
        desc = raw_data.get("description")
        meta = raw_data.get("metadata") or {}
        if isinstance(meta, str):
            meta = {}

        # Determine statuses per ADR-006: explicit status override > raw node > default
        exec_status = e_map.get(nid) or raw_data.get("execution_status") or "COMPLETED_SUCCESS"
        qual_health = q_map.get(nid) or raw_data.get("quality_health") or "HEALTHY"

        flow_data: dict[str, Any] = {
            "label": name,
            "type": node_type,
            "dataset_id": dataset_id,
            "execution_status": exec_status,
            "quality_health": qual_health,
            "owner": owner,
            "description": desc,
            **meta,
        }

        react_nodes.append(
            ReactFlowNode(
                id=nid,
                name=name,
                type=node_type,
                dataset_id=str(dataset_id) if dataset_id else None,
                execution_status=str(exec_status),
                quality_health=str(qual_health),
                position=NodePosition(x=float(pos["x"]), y=float(pos["y"])),
                owner=str(owner) if owner else None,
                description=str(desc) if desc else None,
                metadata=meta if isinstance(meta, dict) else {},
                data=flow_data,
            )
        )

    react_edges: list[ReactFlowEdge] = []
    for u, v in graph.edges:
        edge_data = graph.get_edge(u, v)
        edge_id = str(edge_data.get("id", f"e_{u}_to_{v}"))
        dep_type = str(edge_data.get("dependency_type", "DIRECT_INPUT"))

        # Animate edge if source or target has corrupted/degraded status
        source_corrupted = q_map.get(u) in ("CORRUPTED", "DEGRADED", "CONFIRMED_FAILED")
        target_corrupted = q_map.get(v) in (
            "CORRUPTED",
            "DEGRADED",
            "DIRECTLY_AFFECTED",
            "POTENTIALLY_AFFECTED",
        )
        is_animated = source_corrupted and target_corrupted

        react_edges.append(
            ReactFlowEdge(
                id=edge_id,
                source=u,
                target=v,
                dependency_type=dep_type,
                animated=is_animated,
            )
        )

    return LineageGraphResponse(
        scenario_id=effective_scenario,
        nodes=react_nodes,
        edges=react_edges,
    )
