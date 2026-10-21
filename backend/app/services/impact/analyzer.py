"""Downstream impact analysis service and blast radius classifier."""

from __future__ import annotations

import json

import networkx as nx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import NotFoundError
from app.models.validation import ValidationFinding, ValidationRule
from app.schemas.impact import (
    AffectedAsset,
    AssetImpactStatus,
    BlastRadiusReport,
    ImpactSummary,
    ImpactTargetType,
)
from app.schemas.lineage import LineageNodeType
from app.services.lineage.graph import LineageGraph


class ImpactAnalysisService:
    """Domain service for calculating downstream blast radius, dependency breadcrumbs,

    and asset impact classifications from any failed check, dataset, or node.
    """

    @classmethod
    def resolve_target_node(
        cls,
        graph: LineageGraph,
        target_id: str,
        target_type: ImpactTargetType | str = ImpactTargetType.AUTO,
        scenario_id: str | None = None,
        db: Session | None = None,
    ) -> tuple[str, str | None]:
        """Resolve a target identifier (finding ID, rule ID, dataset name/ID, or node ID)

        to a root lineage node ID and its associated dataset ID.

        Args:
            graph: The LineageGraph instance to search.
            target_id: Entity identifier to resolve.
            target_type: Expected target type, or AUTO to infer.
            scenario_id: Optional scenario ID for scenario file lookup.
            db: Optional active SQLAlchemy database session for DB entity lookup.

        Returns:
            Tuple of (root_node_id, root_dataset_id).

        Raises:
            NotFoundError: If target_id cannot be resolved.
        """
        # 1. Direct Lineage Node ID match
        if graph.has_node(target_id):
            node_data = graph.get_node(target_id)
            ds_id = node_data.get("dataset_id")
            return target_id, str(ds_id) if ds_id else None

        # 2. Match against node attributes (dataset_id, name, file basename)
        clean_target = target_id.strip()
        for nid in graph.nodes:
            ndata = graph.get_node(nid)
            # Check dataset_id
            if ndata.get("dataset_id") == clean_target:
                return nid, clean_target
            # Check exact name (e.g. 'orders.csv')
            if ndata.get("name") == clean_target:
                return nid, ndata.get("dataset_id")
            # Check name ignoring case
            if str(ndata.get("name", "")).lower() == clean_target.lower():
                return nid, ndata.get("dataset_id")

        # Strip .csv or .json if user passed filename like 'orders.csv'
        if clean_target.endswith((".csv", ".json")):
            stem = clean_target.rsplit(".", 1)[0]
            for nid in graph.nodes:
                ndata = graph.get_node(nid)
                if ndata.get("dataset_id") == stem:
                    return nid, stem

        # 3. Database lookup for finding or rule if DB session is supplied
        if db is not None:
            # Check if target_id matches a ValidationFinding ID
            stmt_finding = select(ValidationFinding).where(ValidationFinding.id == clean_target)
            finding = db.execute(stmt_finding).scalar_one_or_none()
            if finding and finding.dataset_id:
                for nid in graph.nodes:
                    if graph.get_node(nid).get("dataset_id") == finding.dataset_id:
                        return nid, finding.dataset_id

            # Check if target_id matches a ValidationRule ID (e.g. 'VAL-ORD-001')
            stmt_rule = select(ValidationRule).where(ValidationRule.id == clean_target)
            rule = db.execute(stmt_rule).scalar_one_or_none()
            if rule and rule.dataset_id:
                for nid in graph.nodes:
                    if graph.get_node(nid).get("dataset_id") == rule.dataset_id:
                        return nid, rule.dataset_id

        # 4. Fallback: inspect scenario files in data/scenarios/<scenario_id>
        effective_scenario = scenario_id or graph.scenario_id or "monday_revenue_mystery"
        scenario_dir = settings.scenarios_dir / effective_scenario
        if scenario_dir.exists():
            # Check rules.json for matching rule ID
            rules_path = scenario_dir / "rules.json"
            if rules_path.exists():
                try:
                    with open(rules_path, encoding="utf-8") as f:
                        rules_data = json.load(f)
                    for r in rules_data.get("rules", []):
                        if r.get("id") == clean_target:
                            rule_ds = r.get("dataset_id")
                            for nid in graph.nodes:
                                if graph.get_node(nid).get("dataset_id") == rule_ds:
                                    return nid, rule_ds
                except Exception:
                    pass

            # Check scenario.json for dataset ID or dataset name
            scenario_path = scenario_dir / "scenario.json"
            if scenario_path.exists():
                try:
                    with open(scenario_path, encoding="utf-8") as f:
                        s_data = json.load(f)
                    for ds in s_data.get("datasets", []):
                        if ds.get("id") == clean_target or ds.get("name") == clean_target:
                            ds_id = ds.get("id")
                            for nid in graph.nodes:
                                if graph.get_node(nid).get("dataset_id") == ds_id:
                                    return nid, ds_id
                except Exception:
                    pass

        raise NotFoundError(
            code="TARGET_NOT_FOUND",
            message=(
                f"Lineage target '{target_id}' could not be resolved to any node, "
                f"dataset, finding, or rule in scenario '{effective_scenario}'."
            ),
            details={
                "target_id": target_id,
                "target_type": str(target_type),
                "scenario_id": effective_scenario,
            },
        )

    @classmethod
    def trace_impact(
        cls,
        target_id: str,
        target_type: ImpactTargetType | str = ImpactTargetType.AUTO,
        scenario_id: str | None = None,
        graph: LineageGraph | None = None,
        include_transformations: bool = False,
        include_root: bool = True,
        db: Session | None = None,
    ) -> BlastRadiusReport:
        """Trace the downstream impact blast radius originating from target_id.

        Calculates shortest directed paths from the resolved root node to all downstream
        reachable assets, categorizes each asset into an impact tier (CONFIRMED_FAILED,
        DIRECTLY_AFFECTED, or POTENTIALLY_AFFECTED), and generates dependency breadcrumbs.

        Args:
            target_id: Identifier of target (e.g. 'orders.csv', 'VAL-ORD-001', 'src_orders').
            target_type: Expected target type (FINDING, DATASET, NODE, RULE, AUTO).
            scenario_id: Target scenario identifier.
            graph: Optional pre-loaded LineageGraph. If None, loaded from db or scenario file.
            include_transformations: Whether to include compute steps in affected assets.
            include_root: Whether to include the root failed asset in the affected assets list.
            db: Optional active SQLAlchemy database session.

        Returns:
            BlastRadiusReport conforming to the API contracts.
        """
        effective_scenario = scenario_id or "monday_revenue_mystery"

        # Resolve or load LineageGraph if not provided
        if graph is None:
            if db is not None:
                try:
                    graph = LineageGraph.from_db(db, effective_scenario)
                except Exception:
                    scenario_file = settings.scenarios_dir / effective_scenario / "scenario.json"
                    graph = LineageGraph.from_scenario_file(scenario_file)
            else:
                scenario_file = settings.scenarios_dir / effective_scenario / "scenario.json"
                graph = LineageGraph.from_scenario_file(scenario_file)

        # Resolve target to root node
        root_node_id, root_dataset_id = cls.resolve_target_node(
            graph=graph,
            target_id=target_id,
            target_type=target_type,
            scenario_id=effective_scenario,
            db=db,
        )

        root_data = graph.get_node(root_node_id)
        root_name = str(root_data.get("name", root_node_id))
        root_type = str(root_data.get("type", LineageNodeType.SOURCE_DATASET.value))

        affected_items: list[AffectedAsset] = []

        # 1. Optionally include root entity as CONFIRMED_FAILED
        if include_root:
            affected_items.append(
                AffectedAsset(
                    node_id=root_node_id,
                    name=root_name,
                    type=root_type,
                    impact_status=AssetImpactStatus.CONFIRMED_FAILED,
                    distance=0,
                    dependency_path=[root_node_id],
                    dependency_path_names=[root_name],
                    explanation=(
                        f"Root failed asset '{root_name}' ({root_type}) where defect originates."
                    ),
                )
            )

        # 2. Discover all reachable downstream descendants via NetworkX DiGraph
        descendant_ids = set(nx.descendants(graph._graph, root_node_id))

        for node_id in descendant_ids:
            node_data = graph.get_node(node_id)
            node_type = str(node_data.get("type", LineageNodeType.DERIVED_DATASET.value))
            node_name = str(node_data.get("name", node_id))

            # Skip transformations if caller did not request them
            is_transformation = (
                node_type == LineageNodeType.TRANSFORMATION.value or node_type == "TRANSFORMATION"
            )
            if is_transformation and not include_transformations:
                continue

            # Compute shortest directed path from root to this node
            path: list[str] = list(nx.shortest_path(graph._graph, root_node_id, node_id))
            distance = len(path) - 1

            # Build human-readable name sequence
            path_names = [str(graph.get_node(nid).get("name", nid)) for nid in path]
            explanation_breadcrumb = " -> ".join(path_names)

            # Classify impact status: DIRECTLY_AFFECTED vs POTENTIALLY_AFFECTED
            intermediate_nodes = path[1:-1]
            if len(path) == 2:
                impact_status = AssetImpactStatus.DIRECTLY_AFFECTED
            else:
                intermediate_types = [
                    str(graph.get_node(mid).get("type")) for mid in intermediate_nodes
                ]
                all_transformations = all(
                    t in (LineageNodeType.TRANSFORMATION.value, "TRANSFORMATION")
                    for t in intermediate_types
                )
                if all_transformations:
                    impact_status = AssetImpactStatus.DIRECTLY_AFFECTED
                else:
                    impact_status = AssetImpactStatus.POTENTIALLY_AFFECTED

            affected_items.append(
                AffectedAsset(
                    node_id=node_id,
                    name=node_name,
                    type=node_type,
                    impact_status=impact_status,
                    distance=distance,
                    dependency_path=path,
                    dependency_path_names=path_names,
                    explanation=explanation_breadcrumb,
                )
            )

        # 3. Sort affected assets deterministically: distance ascending, then node_id ascending
        affected_items.sort(key=lambda a: (a.distance, a.node_id))

        # 4. Compute summary counts
        confirmed_count = sum(
            1 for a in affected_items if a.impact_status == AssetImpactStatus.CONFIRMED_FAILED
        )
        directly_count = sum(
            1 for a in affected_items if a.impact_status == AssetImpactStatus.DIRECTLY_AFFECTED
        )
        potentially_count = sum(
            1 for a in affected_items if a.impact_status == AssetImpactStatus.POTENTIALLY_AFFECTED
        )

        return BlastRadiusReport(
            target_id=target_id,
            target_type=str(target_type),
            root_node_id=root_node_id,
            root_dataset_id=root_dataset_id,
            scenario_id=effective_scenario,
            total_affected_assets=len(affected_items),
            impact_summary=ImpactSummary(
                confirmed_failed=confirmed_count,
                directly_affected=directly_count,
                potentially_affected=potentially_count,
                healthy=0,
            ),
            affected_assets=affected_items,
        )

    @classmethod
    def classify_graph_nodes(
        cls,
        graph: LineageGraph,
        failed_node_ids: set[str] | list[str],
    ) -> dict[str, AssetImpactStatus]:
        """Annotate every node in the lineage graph with its overall impact classification

        given a set of confirmed failed root nodes.

        Classification priority:
        1. CONFIRMED_FAILED: If node is directly in failed_node_ids.
        2. DIRECTLY_AFFECTED: If node is a direct consumer of any failed node (or separated
           only by transformations).
        3. POTENTIALLY_AFFECTED: If node is reachable downstream from any failed node.
        4. HEALTHY: Otherwise (unaffected by failures).

        Returns:
            Dictionary mapping node_id -> AssetImpactStatus.
        """
        failed_set = set(failed_node_ids)
        result: dict[str, AssetImpactStatus] = {}

        # Precompute all reachable descendants from failed nodes
        directly_affected_set: set[str] = set()
        potentially_affected_set: set[str] = set()

        for root in failed_set:
            if not graph.has_node(root):
                continue
            descendants = set(nx.descendants(graph._graph, root))
            for desc in descendants:
                if desc in failed_set:
                    continue
                path = list(nx.shortest_path(graph._graph, root, desc))
                intermediate_nodes = path[1:-1]
                if len(path) == 2:
                    directly_affected_set.add(desc)
                else:
                    intermediate_types = [
                        str(graph.get_node(mid).get("type")) for mid in intermediate_nodes
                    ]
                    all_transformations = all(
                        t in (LineageNodeType.TRANSFORMATION.value, "TRANSFORMATION")
                        for t in intermediate_types
                    )
                    if all_transformations:
                        directly_affected_set.add(desc)
                    else:
                        potentially_affected_set.add(desc)

        # If a node was marked both directly and potentially affected from different sources,
        # directly affected takes precedence as the higher severity.
        potentially_affected_set.difference_update(directly_affected_set)

        for nid in graph.nodes:
            if nid in failed_set:
                result[nid] = AssetImpactStatus.CONFIRMED_FAILED
            elif nid in directly_affected_set:
                result[nid] = AssetImpactStatus.DIRECTLY_AFFECTED
            elif nid in potentially_affected_set:
                result[nid] = AssetImpactStatus.POTENTIALLY_AFFECTED
            else:
                result[nid] = AssetImpactStatus.HEALTHY

        return result

    @classmethod
    def build_path_explanation(cls, graph: LineageGraph, path: list[str]) -> str:
        """Build a human-readable dependency chain explanation from a node sequence."""
        names = [str(graph.get_node(nid).get("name", nid)) for nid in path]
        return " -> ".join(names)

    @classmethod
    def get_root_cause_candidates(cls, graph: LineageGraph, target_node_id: str) -> list[str]:
        """Return all upstream origin/source dataset nodes that feed into target_node_id."""
        ancestors = graph.get_upstream_nodes(target_node_id)
        roots: list[str] = []
        for nid in ancestors:
            ndata = graph.get_node(nid)
            ntype = str(ndata.get("type"))
            if (
                ntype
                in (
                    LineageNodeType.SOURCE_DATASET.value,
                    "SOURCE_DATASET",
                )
                or graph.get_direct_upstream(nid) == []
            ):
                roots.append(nid)
        return sorted(roots)
