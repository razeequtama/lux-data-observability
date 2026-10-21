"""Unit tests for downstream impact analysis engine and blast radius classifier."""

from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import NotFoundError
from app.schemas.impact import AssetImpactStatus
from app.schemas.lineage import LineageNodeType
from app.services.impact.analyzer import ImpactAnalysisService
from app.services.ingestion.loader import ScenarioLoaderService
from app.services.lineage.graph import LineageGraph
from app.services.validation.runner import ValidationRunnerService

SCENARIO_ID = "monday_revenue_mystery"


@pytest.fixture
def scenario_file_path() -> Path:
    """Path to the signature scenario.json file."""
    path = settings.scenarios_dir / SCENARIO_ID / "scenario.json"
    assert path.exists(), f"scenario.json not found at {path}"
    return path


@pytest.fixture
def lineage_graph(scenario_file_path: Path) -> LineageGraph:
    """Pre-loaded LineageGraph for the signature scenario."""
    return LineageGraph.from_scenario_file(scenario_file_path)


# =============================================================================
# 1. Acceptance Criteria Verification for orders.csv Blast Radius
# =============================================================================


def test_trace_impact_orders_csv_blast_radius(lineage_graph: LineageGraph) -> None:
    """Verify tracing 'orders.csv' identifies dim_orders as DIRECTLY_AFFECTED,

    and agg_daily_revenue, metric_revenue, report_exec_dash as POTENTIALLY_AFFECTED,
    with complete step-by-step breadcrumb explanations.
    """
    report = ImpactAnalysisService.trace_impact(
        target_id="orders.csv",
        graph=lineage_graph,
        scenario_id=SCENARIO_ID,
        include_transformations=False,
        include_root=True,
    )

    # 1. Root entity verification
    assert report.root_node_id == "src_orders"
    assert report.root_dataset_id == "orders"

    # Map affected assets by node_id
    asset_map = {a.node_id: a for a in report.affected_assets}

    # 2. Total affected data assets:
    # src_orders (CONFIRMED_FAILED), dim_orders (DIRECTLY_AFFECTED),
    # agg_daily_revenue (POTENTIALLY_AFFECTED), metric_revenue (POTENTIALLY_AFFECTED),
    # report_exec_dash (POTENTIALLY_AFFECTED)
    assert len(report.affected_assets) == 5
    assert report.total_affected_assets == 5

    # 3. Acceptance criteria: dim_orders is DIRECTLY_AFFECTED
    dim_orders = asset_map.get("dim_orders")
    assert dim_orders is not None
    assert dim_orders.impact_status == AssetImpactStatus.DIRECTLY_AFFECTED
    assert dim_orders.type == LineageNodeType.DERIVED_DATASET.value
    assert dim_orders.distance == 2
    assert dim_orders.dependency_path == ["src_orders", "tf_orders", "dim_orders"]
    assert "orders.csv" in dim_orders.explanation
    assert "dim_orders" in dim_orders.explanation

    # 4. Acceptance criteria: agg_daily_revenue is POTENTIALLY_AFFECTED
    agg_rev = asset_map.get("agg_daily_revenue")
    assert agg_rev is not None
    assert agg_rev.impact_status == AssetImpactStatus.POTENTIALLY_AFFECTED
    assert agg_rev.type == LineageNodeType.DERIVED_DATASET.value
    assert agg_rev.distance == 4
    assert agg_rev.dependency_path == [
        "src_orders",
        "tf_orders",
        "dim_orders",
        "tf_revenue",
        "agg_daily_revenue",
    ]

    # 5. Acceptance criteria: metric_revenue is POTENTIALLY_AFFECTED
    metric_rev = asset_map.get("metric_revenue")
    assert metric_rev is not None
    assert metric_rev.impact_status == AssetImpactStatus.POTENTIALLY_AFFECTED
    assert metric_rev.type == LineageNodeType.METRIC.value
    assert metric_rev.distance == 5
    assert metric_rev.dependency_path == [
        "src_orders",
        "tf_orders",
        "dim_orders",
        "tf_revenue",
        "agg_daily_revenue",
        "metric_revenue",
    ]

    # 6. Acceptance criteria: report_exec_dash is POTENTIALLY_AFFECTED
    report_exec = asset_map.get("report_exec_dash")
    assert report_exec is not None
    assert report_exec.impact_status == AssetImpactStatus.POTENTIALLY_AFFECTED
    assert report_exec.type == LineageNodeType.REPORT.value
    assert report_exec.distance == 6
    assert report_exec.dependency_path == [
        "src_orders",
        "tf_orders",
        "dim_orders",
        "tf_revenue",
        "agg_daily_revenue",
        "metric_revenue",
        "report_exec_dash",
    ]
    assert report_exec.dependency_path_names == [
        "orders.csv",
        "transform_clean_orders",
        "dim_orders",
        "aggregate_daily_revenue",
        "agg_daily_revenue",
        "Metric: Total Daily Revenue",
        "Report: Executive Monday Dashboard",
    ]
    assert report_exec.explanation == " -> ".join(report_exec.dependency_path_names)

    # 7. Disconnected / unaffected nodes are NOT present in affected assets
    unaffected = {
        "src_inventory",
        "tf_inventory",
        "dim_inventory",
        "metric_inventory",
        "report_stock_alert",
        "src_products",
        "src_order_items",
        "tf_items",
        "fct_order_items",
    }
    for uid in unaffected:
        assert uid not in asset_map, f"Unaffected node '{uid}' should not be in affected assets"

    # 8. Summary counts check
    assert report.impact_summary.confirmed_failed == 1
    assert report.impact_summary.directly_affected == 1
    assert report.impact_summary.potentially_affected == 3


def test_trace_impact_target_formats(lineage_graph: LineageGraph) -> None:
    """Verify impact trace produces identical results across equivalent target formats."""
    rep_fn = ImpactAnalysisService.trace_impact("orders.csv", graph=lineage_graph)
    rep_ds = ImpactAnalysisService.trace_impact("orders", graph=lineage_graph)
    rep_nd = ImpactAnalysisService.trace_impact("src_orders", graph=lineage_graph)

    assert rep_fn.root_node_id == rep_ds.root_node_id == rep_nd.root_node_id == "src_orders"
    assert rep_fn.total_affected_assets == rep_ds.total_affected_assets == 5
    assert rep_nd.total_affected_assets == 5
    fn_ids = [a.node_id for a in rep_fn.affected_assets]
    ds_ids = [a.node_id for a in rep_ds.affected_assets]
    assert fn_ids == ds_ids


# =============================================================================
# 2. Rule and Finding Target Resolution (VAL-ORD-001)
# =============================================================================


def test_trace_impact_by_rule_id_val_ord_001(lineage_graph: LineageGraph) -> None:
    """Verify impact tracing by validation rule ID 'VAL-ORD-001' maps to orders dataset."""
    report = ImpactAnalysisService.trace_impact(
        target_id="VAL-ORD-001",
        graph=lineage_graph,
        scenario_id=SCENARIO_ID,
    )

    assert report.root_node_id == "src_orders"
    assert report.root_dataset_id == "orders"
    assert report.total_affected_assets == 5

    expected_ids = [
        "src_orders",
        "dim_orders",
        "agg_daily_revenue",
        "metric_revenue",
        "report_exec_dash",
    ]
    assert [a.node_id for a in report.affected_assets] == expected_ids

    # Verify classifications
    status_map = {a.node_id: a.impact_status for a in report.affected_assets}
    assert status_map["src_orders"] == AssetImpactStatus.CONFIRMED_FAILED
    assert status_map["dim_orders"] == AssetImpactStatus.DIRECTLY_AFFECTED
    assert status_map["agg_daily_revenue"] == AssetImpactStatus.POTENTIALLY_AFFECTED
    assert status_map["metric_revenue"] == AssetImpactStatus.POTENTIALLY_AFFECTED
    assert status_map["report_exec_dash"] == AssetImpactStatus.POTENTIALLY_AFFECTED


def test_trace_impact_from_db_finding(db_session: Session) -> None:
    """Verify impact tracing resolves a database ValidationFinding entity to its lineage source."""
    # 1. Load scenario into SQLite
    ScenarioLoaderService.load_scenario(SCENARIO_ID, "defective", db_session)

    # 2. Run validations to populate findings in SQLite
    run_response = ValidationRunnerService.execute_validation_run(
        scenario_id=SCENARIO_ID,
        db=db_session,
    )
    assert run_response.failed_checks == 4

    # 3. Retrieve finding for orders dataset
    total, findings = ValidationRunnerService.list_run_findings(
        run_id=run_response.id,
        dataset_id="orders",
        db=db_session,
    )
    assert total >= 1
    finding_id = findings[0].id

    # 4. Trace impact using DB session
    report = ImpactAnalysisService.trace_impact(
        target_id=finding_id,
        target_type="FINDING",
        scenario_id=SCENARIO_ID,
        db=db_session,
    )

    assert report.root_node_id == "src_orders"
    assert report.root_dataset_id == "orders"
    assert report.total_affected_assets == 5


# =============================================================================
# 3. Alternative Scenario Branches (Order Items & Inventory)
# =============================================================================


def test_trace_impact_order_items(lineage_graph: LineageGraph) -> None:
    """Verify tracing order_items.csv affects fct_order_items directly and revenue metrics."""
    report = ImpactAnalysisService.trace_impact("order_items.csv", graph=lineage_graph)

    assert report.root_node_id == "src_order_items"
    assert report.root_dataset_id == "order_items"

    asset_map = {a.node_id: a for a in report.affected_assets}

    # fct_order_items is DIRECTLY_AFFECTED (only tf_items intermediate)
    fct = asset_map["fct_order_items"]
    assert fct.impact_status == AssetImpactStatus.DIRECTLY_AFFECTED
    assert fct.distance == 2
    assert fct.dependency_path == ["src_order_items", "tf_items", "fct_order_items"]

    # Downstream revenue models are POTENTIALLY_AFFECTED
    assert asset_map["agg_daily_revenue"].impact_status == AssetImpactStatus.POTENTIALLY_AFFECTED
    assert asset_map["metric_revenue"].impact_status == AssetImpactStatus.POTENTIALLY_AFFECTED
    assert asset_map["report_exec_dash"].impact_status == AssetImpactStatus.POTENTIALLY_AFFECTED

    # Inventory branch is NOT affected
    assert "src_inventory" not in asset_map
    assert "report_stock_alert" not in asset_map
    # Orders source is NOT affected
    assert "src_orders" not in asset_map
    assert "dim_orders" not in asset_map


def test_trace_impact_inventory(lineage_graph: LineageGraph) -> None:
    """Verify tracing inventory.csv strictly affects the inventory branch."""
    report = ImpactAnalysisService.trace_impact("inventory.csv", graph=lineage_graph)

    assert report.root_node_id == "src_inventory"
    assert report.root_dataset_id == "inventory"

    asset_map = {a.node_id: a for a in report.affected_assets}
    assert len(asset_map) == 4

    # dim_inventory is DIRECTLY_AFFECTED
    assert asset_map["dim_inventory"].impact_status == AssetImpactStatus.DIRECTLY_AFFECTED
    assert asset_map["dim_inventory"].distance == 2

    # metric_inventory and report_stock_alert are POTENTIALLY_AFFECTED
    assert asset_map["metric_inventory"].impact_status == AssetImpactStatus.POTENTIALLY_AFFECTED
    assert asset_map["report_stock_alert"].impact_status == AssetImpactStatus.POTENTIALLY_AFFECTED

    # Revenue pipeline is completely untouched
    assert "report_exec_dash" not in asset_map
    assert "metric_revenue" not in asset_map
    assert "src_orders" not in asset_map


# =============================================================================
# 4. Inclusion Flags & Options
# =============================================================================


def test_trace_impact_including_transformations(lineage_graph: LineageGraph) -> None:
    """Verify including transformation nodes includes tf_orders and tf_revenue."""
    report = ImpactAnalysisService.trace_impact(
        target_id="orders.csv",
        graph=lineage_graph,
        include_transformations=True,
        include_root=True,
    )

    asset_map = {a.node_id: a for a in report.affected_assets}

    # Total nodes on orders path:
    # src_orders, tf_orders, dim_orders, tf_revenue, agg_rev, metric_rev, report = 7
    assert len(report.affected_assets) == 7

    # tf_orders is DIRECTLY_AFFECTED at distance 1
    assert "tf_orders" in asset_map
    assert asset_map["tf_orders"].impact_status == AssetImpactStatus.DIRECTLY_AFFECTED
    assert asset_map["tf_orders"].distance == 1

    # tf_revenue is POTENTIALLY_AFFECTED at distance 3
    assert "tf_revenue" in asset_map
    assert asset_map["tf_revenue"].impact_status == AssetImpactStatus.POTENTIALLY_AFFECTED
    assert asset_map["tf_revenue"].distance == 3


def test_trace_impact_excluding_root(lineage_graph: LineageGraph) -> None:
    """Verify include_root=False omits the root node from affected_assets."""
    report = ImpactAnalysisService.trace_impact(
        target_id="orders.csv",
        graph=lineage_graph,
        include_root=False,
    )

    asset_ids = [a.node_id for a in report.affected_assets]
    assert "src_orders" not in asset_ids
    assert len(report.affected_assets) == 4
    assert report.impact_summary.confirmed_failed == 0
    assert report.impact_summary.directly_affected == 1
    assert report.impact_summary.potentially_affected == 3


def test_trace_terminal_leaf_node(lineage_graph: LineageGraph) -> None:
    """Verify tracing a terminal node (e.g. report_exec_dash) has zero downstream assets."""
    report = ImpactAnalysisService.trace_impact(
        target_id="report_exec_dash",
        graph=lineage_graph,
        include_root=True,
    )

    assert report.root_node_id == "report_exec_dash"
    assert report.total_affected_assets == 1
    assert report.affected_assets[0].node_id == "report_exec_dash"
    assert report.affected_assets[0].impact_status == AssetImpactStatus.CONFIRMED_FAILED
    assert report.impact_summary.directly_affected == 0
    assert report.impact_summary.potentially_affected == 0


# =============================================================================
# 5. Full Graph Node Classification & Root Causes
# =============================================================================


def test_classify_graph_nodes_full_graph(lineage_graph: LineageGraph) -> None:
    """Verify classifying the full graph marks unaffected nodes as HEALTHY."""
    classification = ImpactAnalysisService.classify_graph_nodes(
        graph=lineage_graph,
        failed_node_ids={"src_orders"},
    )

    assert classification["src_orders"] == AssetImpactStatus.CONFIRMED_FAILED
    assert classification["dim_orders"] == AssetImpactStatus.DIRECTLY_AFFECTED
    assert classification["agg_daily_revenue"] == AssetImpactStatus.POTENTIALLY_AFFECTED
    assert classification["metric_revenue"] == AssetImpactStatus.POTENTIALLY_AFFECTED
    assert classification["report_exec_dash"] == AssetImpactStatus.POTENTIALLY_AFFECTED

    # Disconnected inventory nodes are HEALTHY
    assert classification["src_inventory"] == AssetImpactStatus.HEALTHY
    assert classification["dim_inventory"] == AssetImpactStatus.HEALTHY
    assert classification["metric_inventory"] == AssetImpactStatus.HEALTHY
    assert classification["report_stock_alert"] == AssetImpactStatus.HEALTHY

    # Products source is HEALTHY
    assert classification["src_products"] == AssetImpactStatus.HEALTHY


def test_get_root_cause_candidates(lineage_graph: LineageGraph) -> None:
    """Verify upstream origin candidates for report_exec_dash include all 3 source tables."""
    roots = ImpactAnalysisService.get_root_cause_candidates(lineage_graph, "report_exec_dash")
    assert roots == ["src_order_items", "src_orders", "src_products"]

    # Stock alert traces strictly to inventory
    stock_roots = ImpactAnalysisService.get_root_cause_candidates(
        lineage_graph, "report_stock_alert"
    )
    assert stock_roots == ["src_inventory"]


def test_target_not_found_raises_error(lineage_graph: LineageGraph) -> None:
    """Verify NotFoundError is raised when an unresolvable target is provided."""
    with pytest.raises(NotFoundError) as exc_info:
        ImpactAnalysisService.trace_impact("non_existent_target_123", graph=lineage_graph)

    assert exc_info.value.code == "TARGET_NOT_FOUND"


# =============================================================================
# 6. Multi-Path Shortest Distance & Deduplication Edge Case
# =============================================================================


def test_multi_path_shortest_path_and_deduplication() -> None:
    """Verify that when multiple paths lead to the same downstream asset,

    the shortest path is chosen and the asset appears exactly once.
    """
    custom_graph = LineageGraph(name="test_diamond_graph")
    # Topology:
    # Root R
    # Path 1 (length 2): R -> A -> Dest
    # Path 2 (length 3): R -> B -> C -> Dest
    custom_graph.add_node("R", name="Root", type=LineageNodeType.SOURCE_DATASET.value)
    custom_graph.add_node("A", name="A_Trans", type=LineageNodeType.TRANSFORMATION.value)
    custom_graph.add_node("B", name="B_Trans", type=LineageNodeType.TRANSFORMATION.value)
    custom_graph.add_node("C", name="C_Derived", type=LineageNodeType.DERIVED_DATASET.value)
    custom_graph.add_node("Dest", name="Destination", type=LineageNodeType.REPORT.value)

    custom_graph.add_edge("R", "A")
    custom_graph.add_edge("A", "Dest")
    custom_graph.add_edge("R", "B")
    custom_graph.add_edge("B", "C")
    custom_graph.add_edge("C", "Dest")

    report = ImpactAnalysisService.trace_impact("R", graph=custom_graph, include_root=True)

    dest_assets = [a for a in report.affected_assets if a.node_id == "Dest"]
    # Asset is deduplicated: appears exactly once
    assert len(dest_assets) == 1
    dest = dest_assets[0]

    # Distance is 2 (shortest path via A: R -> A -> Dest)
    assert dest.distance == 2
    assert dest.dependency_path == ["R", "A", "Dest"]
    # Since intermediate node A is a TRANSFORMATION, Dest is DIRECTLY_AFFECTED
    assert dest.impact_status == AssetImpactStatus.DIRECTLY_AFFECTED
