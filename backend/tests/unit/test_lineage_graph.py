"""Unit tests for LineageGraph domain engine and graph integrity validator."""

from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import CyclicDependencyError, LineageIntegrityError, NotFoundError
from app.schemas.lineage import LineageNodeType
from app.services.ingestion.loader import ScenarioLoaderService
from app.services.lineage.graph import LineageGraph

SCENARIO_ID = "monday_revenue_mystery"


@pytest.fixture
def scenario_file_path() -> Path:
    """Path to the signature scenario.json file."""
    path = settings.scenarios_dir / SCENARIO_ID / "scenario.json"
    assert path.exists(), f"scenario.json not found at {path}"
    return path


# =============================================================================
# 1. Signature Scenario Graph Ingestion & Structural Verification
# =============================================================================


def test_scenario_graph_loads_cleanly(scenario_file_path: Path) -> None:
    """Verify the 16-node and 14-edge scenario graph loads cleanly without errors."""
    graph = LineageGraph.from_scenario_file(scenario_file_path)

    assert graph.node_count == 16, f"Expected 16 nodes, got {graph.node_count}"
    assert graph.edge_count == 14, f"Expected 14 edges, got {graph.edge_count}"

    summary = graph.validate_integrity()
    assert summary.is_valid is True
    assert summary.is_dag is True
    assert len(summary.cycles) == 0
    assert len(summary.dangling_edges) == 0
    assert len(summary.errors) == 0


def test_scenario_graph_loads_from_db(db_session: Session) -> None:
    """Verify graph can be seeded directly from database lineage records."""
    # First load scenario into SQLite session
    ScenarioLoaderService.load_scenario(SCENARIO_ID, "defective", db_session)

    graph = LineageGraph.from_db(db_session, SCENARIO_ID)
    assert graph.node_count == 16
    assert graph.edge_count == 14

    summary = graph.validate_integrity()
    assert summary.is_valid is True
    assert summary.is_dag is True


def test_scenario_nodes_contain_correct_metadata(scenario_file_path: Path) -> None:
    """Verify nodes preserve all declared attributes and types."""
    graph = LineageGraph.from_scenario_file(scenario_file_path)

    # Check source nodes
    src_orders = graph.get_node_data("src_orders")
    assert src_orders.name == "orders.csv"
    assert src_orders.type == LineageNodeType.SOURCE_DATASET.value
    assert src_orders.dataset_id == "orders"

    # Check transformation nodes
    tf_revenue = graph.get_node_data("tf_revenue")
    assert tf_revenue.type == LineageNodeType.TRANSFORMATION.value
    assert tf_revenue.metadata.get("engine") == "SQL"

    # Check report nodes
    report_exec = graph.get_node_data("report_exec_dash")
    assert report_exec.type == LineageNodeType.REPORT.value
    assert "Executive" in report_exec.name


# =============================================================================
# 2. Upstream Ancestor & Downstream Descendant Traversal
# =============================================================================


def test_report_exec_dash_upstream_ancestors(scenario_file_path: Path) -> None:
    """Verify upstream ancestors of report_exec_dash include orders and order_items."""
    graph = LineageGraph.from_scenario_file(scenario_file_path)

    upstream_nodes = graph.get_upstream_nodes("report_exec_dash")
    # Must include source dataset nodes for orders, order_items, products
    assert "src_orders" in upstream_nodes
    assert "src_order_items" in upstream_nodes
    assert "src_products" in upstream_nodes

    # Must include intermediate transformations and derived tables
    assert "tf_orders" in upstream_nodes
    assert "tf_items" in upstream_nodes
    assert "dim_orders" in upstream_nodes
    assert "fct_order_items" in upstream_nodes
    assert "tf_revenue" in upstream_nodes
    assert "agg_daily_revenue" in upstream_nodes
    assert "metric_revenue" in upstream_nodes

    # Must NOT include disconnected inventory nodes
    assert "src_inventory" not in upstream_nodes
    assert "dim_inventory" not in upstream_nodes
    assert "report_stock_alert" not in upstream_nodes

    # Verify upstream dataset IDs explicitly resolve to 'orders' and 'order_items'
    upstream_dataset_ids = graph.get_upstream_dataset_ids("report_exec_dash")
    assert "orders" in upstream_dataset_ids
    assert "order_items" in upstream_dataset_ids
    assert "products" in upstream_dataset_ids
    assert "inventory" not in upstream_dataset_ids


def test_report_stock_alert_upstream_ancestors(scenario_file_path: Path) -> None:
    """Verify upstream ancestors of report_stock_alert trace strictly to inventory."""
    graph = LineageGraph.from_scenario_file(scenario_file_path)

    upstream_nodes = graph.get_upstream_nodes("report_stock_alert")
    assert upstream_nodes == {"src_inventory", "tf_inventory", "dim_inventory", "metric_inventory"}

    upstream_datasets = graph.get_upstream_dataset_ids("report_stock_alert")
    assert upstream_datasets == {"inventory"}


def test_src_orders_downstream_descendants(scenario_file_path: Path) -> None:
    """Verify downstream traversal from src_orders traverses to report_exec_dash."""
    graph = LineageGraph.from_scenario_file(scenario_file_path)

    downstream_nodes = graph.get_downstream_nodes("src_orders")
    expected_downstream = {
        "tf_orders",
        "dim_orders",
        "tf_revenue",
        "agg_daily_revenue",
        "metric_revenue",
        "report_exec_dash",
    }
    assert expected_downstream.issubset(downstream_nodes)
    # Does not include order_items transformation
    assert "tf_items" not in downstream_nodes
    # Does not include inventory branch
    assert "report_stock_alert" not in downstream_nodes


def test_direct_predecessors_and_successors(scenario_file_path: Path) -> None:
    """Verify immediate upstream and downstream connections."""
    graph = LineageGraph.from_scenario_file(scenario_file_path)

    # tf_revenue joins dim_orders and fct_order_items
    direct_upstream = set(graph.get_direct_upstream("tf_revenue"))
    assert direct_upstream == {"dim_orders", "fct_order_items"}

    # tf_revenue feeds agg_daily_revenue
    direct_downstream = graph.get_direct_downstream("tf_revenue")
    assert direct_downstream == ["agg_daily_revenue"]


# =============================================================================
# 3. Directed Acyclic Graph (DAG) Integrity & Cycle Detection
# =============================================================================


def test_cycle_rejection_two_node_loop() -> None:
    """Verify cyclic dependency A -> B -> A raises CyclicDependencyError with cycle path."""
    graph = LineageGraph()
    graph.add_node("A", name="Node A")
    graph.add_node("B", name="Node B")
    graph.add_edge("A", "B")
    graph.add_edge("B", "A")

    # validate_integrity should capture the cycle
    summary = graph.validate_integrity()
    assert summary.is_valid is False
    assert summary.is_dag is False
    assert len(summary.cycles) > 0
    cycle = summary.cycles[0]
    assert cycle in (["A", "B", "A"], ["B", "A", "B"])

    # validate() should raise CyclicDependencyError detailing the path
    with pytest.raises(CyclicDependencyError) as exc_info:
        graph.validate()

    assert exc_info.value.code == "CYCLIC_DEPENDENCY"
    assert exc_info.value.cycle_path in (["A", "B", "A"], ["B", "A", "B"])
    assert "Lineage graph contains cyclic dependencies" in exc_info.value.message


def test_cycle_rejection_self_loop() -> None:
    """Verify self-loop A -> A raises CyclicDependencyError."""
    graph = LineageGraph()
    graph.add_node("A", name="Node A")
    graph.add_edge("A", "A")

    summary = graph.validate_integrity()
    assert summary.is_valid is False
    assert summary.is_dag is False

    with pytest.raises(CyclicDependencyError) as exc_info:
        graph.validate()

    assert exc_info.value.cycle_path == ["A", "A"]


def test_cycle_rejection_multi_hop_loop() -> None:
    """Verify multi-hop cycle A -> B -> C -> D -> B raises CyclicDependencyError."""
    graph = LineageGraph()
    for n in ["A", "B", "C", "D"]:
        graph.add_node(n, name=f"Node {n}")

    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    graph.add_edge("C", "D")
    graph.add_edge("D", "B")  # Creates cycle B -> C -> D -> B

    with pytest.raises(CyclicDependencyError) as exc_info:
        graph.validate()

    cycle = exc_info.value.cycle_path
    # The cycle subpath must be B, C, D, B (in some cyclic permutation)
    assert set(cycle) == {"B", "C", "D"}
    assert cycle[0] == cycle[-1]


def test_cycle_rejection_on_from_scenario_dict() -> None:
    """Verify factory loader automatically validates and rejects cyclic definitions."""
    cyclic_scenario = {
        "id": "cyclic_scenario",
        "lineage": {
            "nodes": [
                {"id": "node_1", "name": "Node 1", "type": "SOURCE_DATASET"},
                {"id": "node_2", "name": "Node 2", "type": "TRANSFORMATION"},
            ],
            "edges": [
                {"source": "node_1", "target": "node_2"},
                {"source": "node_2", "target": "node_1"},
            ],
        },
    }

    with pytest.raises(CyclicDependencyError):
        LineageGraph.from_scenario_dict(cyclic_scenario, validate=True)


# =============================================================================
# 4. Dangling Reference & Isolated Node Integrity Checks
# =============================================================================


def test_dangling_edge_detected_when_unregistered_node_referenced() -> None:
    """Verify edge pointing to an unregistered node is caught by integrity validation."""
    graph = LineageGraph()
    graph.add_node("A", name="Node A")
    # Add edge to unregistered 'B' without strict node validation
    graph.add_edge("A", "B", validate_nodes=False)

    summary = graph.validate_integrity()
    assert summary.is_valid is False
    assert len(summary.dangling_edges) == 1
    assert summary.dangling_edges[0] == {"source": "A", "target": "B"}

    with pytest.raises(LineageIntegrityError) as exc_info:
        graph.validate()

    assert exc_info.value.code == "DANGLING_EDGE_REFERENCE"


def test_strict_add_edge_rejects_unregistered_node() -> None:
    """Verify add_edge with validate_nodes=True raises LineageIntegrityError immediately."""
    graph = LineageGraph()
    graph.add_node("A", name="Node A")

    with pytest.raises(LineageIntegrityError) as exc_info:
        graph.add_edge("A", "unregistered_node", validate_nodes=True)

    assert exc_info.value.code == "UNREGISTERED_NODE_REFERENCE"


def test_isolated_node_handling() -> None:
    """Verify isolated nodes are reported as warnings by default, or errors when disallowed."""
    graph = LineageGraph()
    graph.add_node("A", name="Node A")
    graph.add_node("B", name="Node B")
    graph.add_node("isolated_node", name="Isolated Node")
    graph.add_edge("A", "B")

    # With allow_isolated=True (default): valid with warning
    summary = graph.validate_integrity(allow_isolated=True)
    assert summary.is_valid is True
    assert summary.isolated_nodes == ["isolated_node"]
    assert len(summary.warnings) == 1

    # With allow_isolated=False: invalid with error
    summary_strict = graph.validate_integrity(allow_isolated=False)
    assert summary_strict.is_valid is False
    assert len(summary_strict.errors) == 1

    with pytest.raises(LineageIntegrityError):
        graph.validate(allow_isolated=False)


# =============================================================================
# 5. Topological Sort & Graph Path Computations
# =============================================================================


def test_topological_sort_order(scenario_file_path: Path) -> None:
    """Verify topological sort yields an execution order respecting all dependency edges."""
    graph = LineageGraph.from_scenario_file(scenario_file_path)

    order = graph.topological_sort()
    assert len(order) == 16

    # For every edge (u, v), u must appear before v in topological order
    index_map = {node_id: idx for idx, node_id in enumerate(order)}
    for u, v in graph.edges:
        assert index_map[u] < index_map[v], f"Edge violation: {u} -> {v}"


def test_topological_sort_on_cyclic_graph_raises() -> None:
    """Verify topological sort cannot be computed on a cyclic graph."""
    graph = LineageGraph()
    graph.add_node("A")
    graph.add_node("B")
    graph.add_edge("A", "B")
    graph.add_edge("B", "A")

    with pytest.raises(CyclicDependencyError):
        graph.topological_sort()


def test_shortest_path_and_connectivity(scenario_file_path: Path) -> None:
    """Verify path computations and graph reachability."""
    graph = LineageGraph.from_scenario_file(scenario_file_path)

    # Path from src_orders to report_exec_dash
    assert graph.has_path("src_orders", "report_exec_dash") is True
    path = graph.get_shortest_path("src_orders", "report_exec_dash")
    expected_path = [
        "src_orders",
        "tf_orders",
        "dim_orders",
        "tf_revenue",
        "agg_daily_revenue",
        "metric_revenue",
        "report_exec_dash",
    ]
    assert path == expected_path

    # No path between disconnected inventory branch and executive revenue dashboard
    assert graph.has_path("src_inventory", "report_exec_dash") is False
    assert graph.get_shortest_path("src_inventory", "report_exec_dash") == []


def test_root_and_terminal_nodes(scenario_file_path: Path) -> None:
    """Verify source root nodes and sink terminal nodes are correctly identified."""
    graph = LineageGraph.from_scenario_file(scenario_file_path)

    roots = set(graph.get_root_nodes())
    assert roots == {"src_orders", "src_order_items", "src_products", "src_inventory"}

    terminals = set(graph.get_terminal_nodes())
    assert terminals == {"report_exec_dash", "report_stock_alert"}


# =============================================================================
# 6. Edge Cases & Error Boundaries
# =============================================================================


def test_traversal_on_nonexistent_node_raises_not_found(scenario_file_path: Path) -> None:
    """Verify querying upstream or downstream for non-existent node raises NotFoundError."""
    graph = LineageGraph.from_scenario_file(scenario_file_path)

    with pytest.raises(NotFoundError):
        graph.get_upstream_nodes("non_existent_node")

    with pytest.raises(NotFoundError):
        graph.get_downstream_nodes("non_existent_node")

    with pytest.raises(NotFoundError):
        graph.get_node("non_existent_node")


def test_subgraph_extraction(scenario_file_path: Path) -> None:
    """Verify induced subgraph extraction contains only selected nodes and relevant edges."""
    graph = LineageGraph.from_scenario_file(scenario_file_path)

    sub_nodes = ["src_orders", "tf_orders", "dim_orders"]
    subgraph = graph.get_subgraph(sub_nodes)

    assert subgraph.node_count == 3
    assert subgraph.edge_count == 2
    assert subgraph.has_edge("src_orders", "tf_orders")
    assert subgraph.has_edge("tf_orders", "dim_orders")
    assert not subgraph.has_node("tf_revenue")


def test_dynamic_node_and_edge_removal() -> None:
    """Verify removing nodes cascades to incident edges and updates registered nodes."""
    graph = LineageGraph()
    graph.add_node("A")
    graph.add_node("B")
    graph.add_node("C")
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")

    assert graph.node_count == 3
    assert graph.edge_count == 2

    graph.remove_node("B")
    assert graph.node_count == 2
    assert graph.edge_count == 0  # Both incident edges removed
    assert not graph.has_node("B")
    assert graph.has_node("A")
    assert graph.has_node("C")


def test_serialization_to_dict_and_schema(scenario_file_path: Path) -> None:
    """Verify graph serializes cleanly to dict and typed schema."""
    graph = LineageGraph.from_scenario_file(scenario_file_path)

    data_dict = graph.to_dict()
    assert "nodes" in data_dict
    assert "edges" in data_dict
    assert len(data_dict["nodes"]) == 16
    assert len(data_dict["edges"]) == 14

    schema = graph.to_schema()
    assert len(schema.nodes) == 16
    assert len(schema.edges) == 14

