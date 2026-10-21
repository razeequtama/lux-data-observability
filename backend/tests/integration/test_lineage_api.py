"""Integration tests for Lineage DAG and Impact REST API Endpoints (Task T11)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app


@pytest.fixture
def test_client(db_session: Session) -> TestClient:
    """Provide a TestClient with overridden isolated database session."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


@pytest.fixture
def loaded_defective_scenario(test_client: TestClient) -> str:
    """Load defective Monday Revenue Mystery scenario into SQLite and return scenario_id."""
    resp = test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    assert resp.status_code == 200, resp.text
    return "monday_revenue_mystery"


# ---------------------------------------------------------------------------
# 1. GET /api/v1/lineage: Lineage Graph Retrieval & Dagre Layout
# ---------------------------------------------------------------------------


def test_get_lineage_graph_returns_16_nodes_with_valid_positions_acceptance(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Acceptance Criterion: GET /api/v1/lineage returns 16 nodes with valid (x, y) coordinates."""
    resp = test_client.get(f"/api/v1/lineage?scenario_id={loaded_defective_scenario}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["scenario_id"] == loaded_defective_scenario
    nodes = data["nodes"]
    edges = data["edges"]

    # Exactly 16 nodes and 14 edges declared in Monday Revenue Mystery
    assert len(nodes) == 16, f"Expected 16 nodes, got {len(nodes)}"
    assert len(edges) == 14, f"Expected 14 edges, got {len(edges)}"

    # Validate node structure and Dagre-calculated coordinates
    node_positions: dict[str, tuple[float, float]] = {}
    for node in nodes:
        assert "id" in node
        assert "name" in node
        assert "type" in node
        assert "position" in node
        assert isinstance(node["position"]["x"], (int, float))
        assert isinstance(node["position"]["y"], (int, float))
        assert node["position"]["x"] >= 50.0
        assert node["position"]["y"] >= 100.0

        # React Flow node data payload exists
        assert "data" in node
        assert node["data"]["label"] == node["name"]
        assert node["data"]["type"] == node["type"]

        node_positions[node["id"]] = (node["position"]["x"], node["position"]["y"])

    # Topological ordering property in Left-to-Right layout:
    # Upstream node must appear to the left of downstream node (x_upstream < x_downstream)
    assert node_positions["src_orders"][0] < node_positions["tf_orders"][0]
    assert node_positions["tf_orders"][0] < node_positions["dim_orders"][0]
    assert node_positions["dim_orders"][0] < node_positions["tf_revenue"][0]
    assert node_positions["tf_revenue"][0] < node_positions["agg_daily_revenue"][0]
    assert node_positions["agg_daily_revenue"][0] < node_positions["metric_revenue"][0]
    assert node_positions["metric_revenue"][0] < node_positions["report_exec_dash"][0]

    # No coordinate collisions among distinct nodes
    unique_positions = set(node_positions.values())
    assert len(unique_positions) == len(nodes), "Found overlapping node coordinates!"


def test_get_lineage_graph_default_scenario(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """GET /api/v1/lineage without query parameter defaults to monday_revenue_mystery."""
    resp = test_client.get("/api/v1/lineage")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["scenario_id"] == "monday_revenue_mystery"
    assert len(data["nodes"]) == 16


def test_get_lineage_graph_not_found(test_client: TestClient) -> None:
    """GET /api/v1/lineage with non-existent scenario returns 404 error envelope."""
    resp = test_client.get("/api/v1/lineage?scenario_id=unknown_scenario_xyz")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "SCENARIO_NOT_FOUND"


def test_get_lineage_graph_annotates_quality_health_after_validation_run(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Lineage nodes dynamically reflect CORRUPTED vs HEALTHY statuses after validation run."""
    # Execute validation run which flags duplicate orders, orphaned items, negative inventory
    run_resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": loaded_defective_scenario},
    )
    assert run_resp.status_code == 200, run_resp.text

    # Fetch lineage graph
    resp = test_client.get(f"/api/v1/lineage?scenario_id={loaded_defective_scenario}")
    assert resp.status_code == 200
    data = resp.json()

    node_map = {n["id"]: n for n in data["nodes"]}

    # Orders branch should be CORRUPTED
    assert node_map["src_orders"]["quality_health"] == "CORRUPTED"
    assert node_map["tf_orders"]["quality_health"] == "CORRUPTED"
    assert node_map["dim_orders"]["quality_health"] == "CORRUPTED"
    assert node_map["agg_daily_revenue"]["quality_health"] == "CORRUPTED"
    assert node_map["report_exec_dash"]["quality_health"] == "CORRUPTED"

    # Products dataset has clean checks and no upstream defects: HEALTHY
    assert node_map["src_products"]["quality_health"] == "HEALTHY"

    # Edge from src_orders to tf_orders should be animated
    edge_map = {e["id"]: e for e in data["edges"]}
    assert edge_map["src_orders->tf_orders"]["animated"] is True


# ---------------------------------------------------------------------------
# 2. GET /api/v1/lineage/nodes/{id}: Node Details & Direct Connections
# ---------------------------------------------------------------------------


def test_get_lineage_node_details_source_node(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """GET /api/v1/lineage/nodes/src_orders returns direct downstream connections and metadata."""
    resp = test_client.get(
        f"/api/v1/lineage/nodes/src_orders?scenario_id={loaded_defective_scenario}"
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["id"] == "src_orders"
    assert data["name"] == "orders.csv"
    assert data["type"] == "SOURCE_DATASET"
    assert data["dataset_id"] == "orders"
    assert data["scenario_id"] == loaded_defective_scenario
    assert data["direct_upstream_count"] == 0
    assert len(data["upstream_nodes"]) == 0
    assert data["direct_downstream_count"] == 1
    assert data["downstream_nodes"][0]["id"] == "tf_orders"
    assert data["total_ancestors_count"] == 0
    assert data["total_descendants_count"] >= 6


def test_get_lineage_node_details_terminal_report_node(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """GET /api/v1/lineage/nodes/report_exec_dash returns direct upstream connections."""
    resp = test_client.get(
        f"/api/v1/lineage/nodes/report_exec_dash?scenario_id={loaded_defective_scenario}"
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["id"] == "report_exec_dash"
    assert data["type"] == "REPORT"
    assert data["direct_upstream_count"] == 1
    assert data["upstream_nodes"][0]["id"] == "metric_revenue"
    assert data["direct_downstream_count"] == 0
    assert len(data["downstream_nodes"]) == 0
    assert data["total_ancestors_count"] >= 7
    # Upstream storage datasets feeding into executive dashboard
    assert "orders" in data["upstream_dataset_ids"]
    assert "order_items" in data["upstream_dataset_ids"]
    assert "products" in data["upstream_dataset_ids"]


def test_get_lineage_node_details_not_found(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """GET /api/v1/lineage/nodes/{id} with unknown ID returns 404."""
    resp = test_client.get(
        f"/api/v1/lineage/nodes/non_existent_node_xyz?scenario_id={loaded_defective_scenario}"
    )
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "NODE_NOT_FOUND"


# ---------------------------------------------------------------------------
# 3. POST /api/v1/lineage/validate: Graph Integrity Validation
# ---------------------------------------------------------------------------


def test_validate_lineage_stored_scenario_valid(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """POST /api/v1/lineage/validate for loaded scenario returns is_valid=True."""
    resp = test_client.post(
        "/api/v1/lineage/validate",
        json={"scenario_id": loaded_defective_scenario},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["is_valid"] is True
    assert data["is_dag"] is True
    assert data["node_count"] == 16
    assert data["edge_count"] == 14
    assert len(data["cycles"]) == 0
    assert len(data["dangling_edges"]) == 0
    assert len(data["errors"]) == 0


def test_validate_lineage_detects_cycles(test_client: TestClient) -> None:
    """POST /api/v1/lineage/validate with cyclic edges returns is_valid=False and cycles."""
    cyclic_payload = {
        "nodes": [
            {"id": "node_a", "name": "Node A", "type": "TRANSFORMATION"},
            {"id": "node_b", "name": "Node B", "type": "TRANSFORMATION"},
            {"id": "node_c", "name": "Node C", "type": "TRANSFORMATION"},
        ],
        "edges": [
            {"source": "node_a", "target": "node_b"},
            {"source": "node_b", "target": "node_c"},
            {"source": "node_c", "target": "node_a"},
        ],
    }
    resp = test_client.post("/api/v1/lineage/validate", json=cyclic_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["is_valid"] is False
    assert data["is_dag"] is False
    assert len(data["cycles"]) >= 1
    cycle = data["cycles"][0]
    assert cycle[0] == cycle[-1]
    assert any("Cyclic dependency detected" in err for err in data["errors"])


def test_validate_lineage_detects_dangling_edges(test_client: TestClient) -> None:
    """POST /api/v1/lineage/validate with dangling edges returns is_valid=False."""
    dangling_payload = {
        "nodes": [
            {"id": "node_a", "name": "Node A", "type": "TRANSFORMATION"},
        ],
        "edges": [
            {"source": "node_a", "target": "unregistered_node_b"},
        ],
    }
    resp = test_client.post("/api/v1/lineage/validate", json=dangling_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["is_valid"] is False
    assert len(data["dangling_edges"]) == 1
    assert any("Dangling edge" in err for err in data["errors"])


# ---------------------------------------------------------------------------
# 4. POST /api/v1/impact/trace: Downstream Impact Analysis
# ---------------------------------------------------------------------------


def test_trace_impact_from_dataset_orders_acceptance(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Acceptance Criterion: POST /api/v1/impact/trace returns affected asset list."""
    payload = {
        "scenario_id": loaded_defective_scenario,
        "target_type": "DATASET",
        "target_id": "orders.csv",
        "include_transformations": False,
        "include_root": True,
    }
    resp = test_client.post("/api/v1/impact/trace", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["target_id"] == "orders.csv"
    assert data["root_dataset_id"] == "orders"
    assert data["root_node_id"] == "src_orders"

    summary = data["impact_summary"]
    assert summary["confirmed_failed"] == 1
    assert summary["directly_affected"] >= 1
    assert summary["potentially_affected"] >= 2

    affected_assets = data["affected_assets"]
    asset_map = {a["node_id"]: a for a in affected_assets}

    # Root asset is confirmed failed
    assert asset_map["src_orders"]["impact_status"] == "CONFIRMED_FAILED"
    assert asset_map["src_orders"]["distance"] == 0

    # Direct downstream derived dataset
    assert asset_map["dim_orders"]["impact_status"] == "DIRECTLY_AFFECTED"

    # Transitive downstream assets
    assert asset_map["agg_daily_revenue"]["impact_status"] == "POTENTIALLY_AFFECTED"
    assert asset_map["metric_revenue"]["impact_status"] == "POTENTIALLY_AFFECTED"
    assert asset_map["report_exec_dash"]["impact_status"] == "POTENTIALLY_AFFECTED"

    # Verify dependency paths and breadcrumbs
    assert "src_orders" in asset_map["report_exec_dash"]["dependency_path"]
    assert "report_exec_dash" in asset_map["report_exec_dash"]["dependency_path"]
    assert "orders.csv" in asset_map["report_exec_dash"]["explanation"]


def test_trace_impact_from_rule_id(test_client: TestClient, loaded_defective_scenario: str) -> None:
    """POST /api/v1/impact/trace resolving rule ID (VAL-ORD-001) traces impact."""
    payload = {
        "scenario_id": loaded_defective_scenario,
        "target_type": "RULE",
        "target_id": "VAL-ORD-001",
    }
    resp = test_client.post("/api/v1/impact/trace", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["root_node_id"] == "src_orders"
    assert data["root_dataset_id"] == "orders"
    asset_ids = [a["node_id"] for a in data["affected_assets"]]
    assert "report_exec_dash" in asset_ids


def test_trace_impact_from_inventory_node_isolates_branches(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Tracing inventory failure isolates the inventory branch from the orders branch."""
    payload = {
        "scenario_id": loaded_defective_scenario,
        "target_type": "NODE",
        "target_id": "src_inventory",
    }
    resp = test_client.post("/api/v1/impact/trace", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    affected_ids = {a["node_id"] for a in data["affected_assets"]}
    assert "dim_inventory" in affected_ids
    assert "metric_inventory" in affected_ids
    assert "report_stock_alert" in affected_ids

    # Must NOT affect the orders or executive dashboard branches
    assert "dim_orders" not in affected_ids
    assert "report_exec_dash" not in affected_ids


def test_trace_impact_terminal_node(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Tracing impact from a leaf report node produces zero downstream descendants."""
    payload = {
        "scenario_id": loaded_defective_scenario,
        "target_type": "NODE",
        "target_id": "report_exec_dash",
        "include_root": False,
    }
    resp = test_client.post("/api/v1/impact/trace", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["total_affected_assets"] == 0
    assert len(data["affected_assets"]) == 0


def test_trace_impact_with_transformations_included(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """When include_transformations=True, intermediate ETL transformations are included."""
    payload = {
        "scenario_id": loaded_defective_scenario,
        "target_id": "orders",
        "include_transformations": True,
        "include_root": True,
    }
    resp = test_client.post("/api/v1/impact/trace", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    node_ids = {a["node_id"] for a in data["affected_assets"]}
    assert "tf_orders" in node_ids
    assert "tf_revenue" in node_ids


def test_trace_impact_target_not_found(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """POST /api/v1/impact/trace with unknown target returns 404."""
    payload = {
        "scenario_id": loaded_defective_scenario,
        "target_id": "completely_unknown_target_id",
    }
    resp = test_client.post("/api/v1/impact/trace", json=payload)
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "TARGET_NOT_FOUND"
