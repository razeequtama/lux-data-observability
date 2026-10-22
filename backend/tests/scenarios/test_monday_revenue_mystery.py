"""Acceptance Test Suite: Monday Revenue Mystery Signature Scenario.

Implements the end-to-end programmatic verification of the 8-step "Trace the Failure" workflow:
Stage 1: Load scenario fixtures and assert dataset schemas and record counts.
Stage 2: Execute data quality validation rules across defective fixtures (4 failures detected).
Stage 3: Inspect findings and row-level evidence (15 dups, 24 orphaned, 8 neg stock, 1 gap).
Stage 4: Trace lineage DAG, verify graph acyclicity, node coordinates, and upstream ancestors.
Stage 5: Analyze downstream impact blast radius and verify branch isolation.
Stage 6: Inspect pipeline observability and assert dual compute SUCCESS vs data CORRUPTED.
Stage 7: Create investigation workspace and generate CSP-enforced HTML and JSON reports.
Stage 8: Verify recovery with clean fixtures, proving 4 defects are RESOLVED and trust restored.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.main import app


@pytest.fixture
def test_client(db_session: Session) -> Generator[TestClient]:
    """Provide a TestClient with an isolated temporary SQLite database session."""

    def _override_get_db() -> Generator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


# ===========================================================================
# MASTER END-TO-END WORKFLOW ACCEPTANCE TEST: "TRACE THE FAILURE"
# ===========================================================================


def test_monday_revenue_mystery_full_trace_the_failure_e2e(test_client: TestClient) -> None:
    """End-to-End Acceptance Test for 'Monday Revenue Mystery' Signature Scenario.

    Traverses the full 8-step 'Trace the Failure' lifecycle in sequence:
    1. Ingestion: Load defective scenario fixtures (orders, items, products, inventory).
    2. Quality Validation: Execute rule engine, assert 4 failed checks and CORRUPTED health.
    3. Findings & Evidence: Assert exact record counts, sample keys, and row line numbers.
    4. Lineage DAG: Assert 16 nodes, 14 edges, acyclicity, and upstream ancestors.
    5. Downstream Impact: Assert blast radius propagation to Executive Dashboard.
    6. Pipeline Observability: Assert Exit Code 0 (SUCCESS) alongside CORRUPTED data health.
    7. Incident Reporting: Synthesize workspace, generate CSP-safe HTML and JSON artifacts.
    8. Recovery Verification: Swap to clean fixtures, prove 4 RESOLVED checks and restored trust.
    """
    scenario_id = "monday_revenue_mystery"

    # -----------------------------------------------------------------------
    # STAGE 1: Load Scenario / Ingest Dataset Fixtures
    # -----------------------------------------------------------------------
    load_resp = test_client.post(
        f"/api/v1/scenarios/{scenario_id}/load",
        json={"fixture_version": "defective"},
    )
    assert load_resp.status_code == 200, f"Stage 1 failed: {load_resp.text}"
    load_data = load_resp.json()

    assert load_data["scenario_id"] == scenario_id
    assert load_data["active_fixture_version"] == "defective"
    assert len(load_data["loaded_datasets"]) == 4
    assert set(load_data["loaded_datasets"]) == {"orders", "order_items", "products", "inventory"}
    assert load_data["rules_registered"] == 8
    assert load_data["lineage_nodes_loaded"] == 16

    # Verify scenario detail metadata
    scenario_detail_resp = test_client.get(f"/api/v1/scenarios/{scenario_id}")
    assert scenario_detail_resp.status_code == 200
    scenario_meta = scenario_detail_resp.json()
    assert scenario_meta["id"] == scenario_id
    assert scenario_meta["active_fixture_version"] == "defective"

    dataset_counts = {ds["id"]: ds["record_count"] for ds in scenario_meta["datasets"]}
    assert dataset_counts["orders"] == 1250
    assert dataset_counts["order_items"] == 3420
    assert dataset_counts["products"] == 250
    assert dataset_counts["inventory"] == 250
    assert sum(dataset_counts.values()) == 5170

    # -----------------------------------------------------------------------
    # STAGE 2: Execute Quality Validations
    # -----------------------------------------------------------------------
    val_resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": scenario_id},
    )
    assert val_resp.status_code == 200, f"Stage 2 failed: {val_resp.text}"
    val_data = val_resp.json()

    val_run_id = val_data["run_id"]
    assert val_run_id.startswith("val_run_")
    assert val_data["scenario_id"] == scenario_id
    assert val_data["fixture_version"] == "defective"
    assert val_data["status"] == "FAILED"
    assert val_data["total_checks"] == 8
    assert val_data["passed_checks"] == 4
    assert val_data["failed_checks"] == 4
    assert val_data["warning_checks"] == 0
    assert val_data["skipped_checks"] == 0
    assert val_data["error_checks"] == 0

    # Verify run retrieval by ID
    run_lookup_resp = test_client.get(f"/api/v1/validations/runs/{val_run_id}")
    assert run_lookup_resp.status_code == 200
    assert run_lookup_resp.json()["run_id"] == val_run_id

    # -----------------------------------------------------------------------
    # STAGE 3: Inspect Findings & Structured Row Evidence
    # -----------------------------------------------------------------------
    findings_resp = test_client.get(f"/api/v1/validations/runs/{val_run_id}/findings")
    assert findings_resp.status_code == 200, f"Stage 3 failed: {findings_resp.text}"
    findings_data = findings_resp.json()
    assert findings_data["total_findings"] == 8
    findings = findings_data["items"]

    failed_findings = [f for f in findings if f["status"] == "FAILED"]
    assert len(failed_findings) == 4, f"Expected 4 failed findings, got {len(failed_findings)}"
    findings_by_rule = {f["rule_id"]: f for f in failed_findings}

    # Defect 1: Duplicate Orders in orders.csv (VAL-ORD-001, CRITICAL)
    assert "VAL-ORD-001" in findings_by_rule
    f_ord_dup = findings_by_rule["VAL-ORD-001"]
    assert f_ord_dup["severity"] == "CRITICAL"
    assert f_ord_dup["dataset_id"] == "orders"
    assert f_ord_dup["affected_fields"] == ["order_id"]
    assert f_ord_dup["affected_record_count"] == 15
    assert f_ord_dup["total_record_count"] == 1250
    assert "sample_duplicates" in f_ord_dup["evidence"]
    sample_dups = f_ord_dup["evidence"]["sample_duplicates"]
    assert len(sample_dups) == 15
    assert "order_id" in sample_dups[0]
    assert len(sample_dups[0]["row_indices"]) >= 2

    # Defect 2: Broken Foreign Keys in order_items.csv (VAL-ORD-002, HIGH)
    assert "VAL-ORD-002" in findings_by_rule
    f_ord_fk = findings_by_rule["VAL-ORD-002"]
    assert f_ord_fk["severity"] == "HIGH"
    assert f_ord_fk["dataset_id"] == "order_items"
    assert f_ord_fk["affected_fields"] == ["product_id"]
    assert f_ord_fk["affected_record_count"] == 24
    assert f_ord_fk["total_record_count"] == 3420
    assert "sample_orphaned_keys" in f_ord_fk["evidence"]
    orphaned_keys = f_ord_fk["evidence"]["sample_orphaned_keys"]
    assert len(orphaned_keys) == 24
    assert "PRD-9001" in orphaned_keys

    # Defect 3: Negative Stock Quantities in inventory.csv (VAL-INV-001, HIGH)
    assert "VAL-INV-001" in findings_by_rule
    f_inv_range = findings_by_rule["VAL-INV-001"]
    assert f_inv_range["severity"] == "HIGH"
    assert f_inv_range["dataset_id"] == "inventory"
    assert f_inv_range["affected_fields"] == ["quantity_on_hand"]
    assert f_inv_range["affected_record_count"] == 8
    assert f_inv_range["total_record_count"] == 250
    assert "sample_violations" in f_inv_range["evidence"]
    assert len(f_inv_range["evidence"]["sample_violations"]) == 8
    for viol in f_inv_range["evidence"]["sample_violations"]:
        assert viol["observed_value"] < 0
        assert viol["column"] == "quantity_on_hand"

    # Defect 4: Temporal Ingestion Gap in orders.csv (VAL-FRESH-001, MEDIUM)
    assert "VAL-FRESH-001" in findings_by_rule
    f_fresh_gap = findings_by_rule["VAL-FRESH-001"]
    assert f_fresh_gap["severity"] == "MEDIUM"
    assert f_fresh_gap["dataset_id"] == "orders"
    assert f_fresh_gap["affected_record_count"] == 1
    assert "max_gap_hours" in f_fresh_gap["evidence"]
    assert f_fresh_gap["evidence"]["max_gap_hours"] >= 4.0

    # Verify filtering findings by severity & status isolates CRITICAL duplicate finding
    crit_resp = test_client.get(
        f"/api/v1/validations/runs/{val_run_id}/findings?severity=CRITICAL&status=FAILED"
    )
    assert crit_resp.status_code == 200
    crit_data = crit_resp.json()
    assert crit_data["total_findings"] == 1
    assert crit_data["items"][0]["rule_id"] == "VAL-ORD-001"

    # -----------------------------------------------------------------------
    # STAGE 4: Trace Lineage DAG & Graph Integrity
    # -----------------------------------------------------------------------
    lineage_resp = test_client.get(f"/api/v1/lineage?scenario_id={scenario_id}")
    assert lineage_resp.status_code == 200, f"Stage 4 failed: {lineage_resp.text}"
    lineage_data = lineage_resp.json()

    nodes = lineage_data["nodes"]
    edges = lineage_data["edges"]
    assert len(nodes) == 16, f"Expected 16 nodes, got {len(nodes)}"
    assert len(edges) == 14, f"Expected 14 edges, got {len(edges)}"

    # Dagre layout coordinates present for all nodes
    for node in nodes:
        assert "position" in node
        assert isinstance(node["position"]["x"], (int, float))
        assert isinstance(node["position"]["y"], (int, float))

    # Validate DAG structural integrity
    graph_val_resp = test_client.post(
        "/api/v1/lineage/validate",
        json={"scenario_id": scenario_id},
    )
    assert graph_val_resp.status_code == 200
    graph_val = graph_val_resp.json()
    assert graph_val["is_valid"] is True
    assert graph_val["is_dag"] is True
    assert len(graph_val["cycles"]) == 0
    assert len(graph_val["dangling_edges"]) == 0

    # Verify upstream ancestors of Executive Monday Dashboard
    exec_node_resp = test_client.get(
        f"/api/v1/lineage/nodes/report_exec_dash?scenario_id={scenario_id}"
    )
    assert exec_node_resp.status_code == 200
    exec_node = exec_node_resp.json()
    assert exec_node["id"] == "report_exec_dash"
    assert exec_node["type"] == "REPORT"
    assert exec_node["total_ancestors_count"] >= 7
    assert "orders" in exec_node["upstream_dataset_ids"]
    assert "order_items" in exec_node["upstream_dataset_ids"]
    assert "products" in exec_node["upstream_dataset_ids"]

    # -----------------------------------------------------------------------
    # STAGE 5: Analyze Downstream Impact & Blast Radius
    # -----------------------------------------------------------------------
    # Trace impact from root dataset: orders.csv
    impact_resp = test_client.post(
        "/api/v1/impact/trace",
        json={
            "scenario_id": scenario_id,
            "target_type": "DATASET",
            "target_id": "orders.csv",
            "include_transformations": False,
            "include_root": True,
        },
    )
    assert impact_resp.status_code == 200, f"Stage 5 failed: {impact_resp.text}"
    impact_data = impact_resp.json()

    assert impact_data["target_id"] == "orders.csv"
    assert impact_data["root_node_id"] == "src_orders"

    affected_assets = impact_data["affected_assets"]
    asset_by_id = {a["node_id"]: a for a in affected_assets}

    # Root dataset node is CONFIRMED_FAILED
    assert "src_orders" in asset_by_id
    assert asset_by_id["src_orders"]["impact_status"] == "CONFIRMED_FAILED"

    # Immediate derived dataset is DIRECTLY_AFFECTED
    assert "dim_orders" in asset_by_id
    assert asset_by_id["dim_orders"]["impact_status"] == "DIRECTLY_AFFECTED"

    # Downstream metrics and reports are POTENTIALLY_AFFECTED
    assert "agg_daily_revenue" in asset_by_id
    assert asset_by_id["agg_daily_revenue"]["impact_status"] == "POTENTIALLY_AFFECTED"

    assert "metric_revenue" in asset_by_id
    assert asset_by_id["metric_revenue"]["impact_status"] == "POTENTIALLY_AFFECTED"

    assert "report_exec_dash" in asset_by_id
    assert asset_by_id["report_exec_dash"]["impact_status"] == "POTENTIALLY_AFFECTED"

    # Assert dependency path connects src_orders to executive dashboard
    exec_path = asset_by_id["report_exec_dash"]["dependency_path"]
    assert exec_path[0] == "src_orders"
    assert exec_path[-1] == "report_exec_dash"
    assert "orders.csv" in asset_by_id["report_exec_dash"]["explanation"]

    # Assert inventory failure is isolated from the orders branch
    inv_impact_resp = test_client.post(
        "/api/v1/impact/trace",
        json={
            "scenario_id": scenario_id,
            "target_type": "NODE",
            "target_id": "src_inventory",
            "include_transformations": False,
        },
    )
    assert inv_impact_resp.status_code == 200
    inv_assets = {a["node_id"] for a in inv_impact_resp.json()["affected_assets"]}
    assert "dim_inventory" in inv_assets
    assert "metric_inventory" in inv_assets
    assert "report_stock_alert" in inv_assets
    assert "report_exec_dash" not in inv_assets  # Executive Dashboard is unaffected by inventory

    # -----------------------------------------------------------------------
    # STAGE 6: Inspect Pipeline Observability & Dual-Dimension Tracking
    # -----------------------------------------------------------------------
    pipe_runs_resp = test_client.get(f"/api/v1/pipelines/runs?scenario_id={scenario_id}")
    assert pipe_runs_resp.status_code == 200, f"Stage 6 failed: {pipe_runs_resp.text}"
    pipe_runs = pipe_runs_resp.json()
    assert len(pipe_runs) == 3

    # Inspect the overnight run (pipe_run_20261020_0200)
    overnight_run = next((r for r in pipe_runs if r["id"] == "pipe_run_20261020_0200"), None)
    assert overnight_run is not None

    # CRITICAL ACCEPTANCE ASSERTION: Dual dimension execution vs data quality
    assert overnight_run["execution_status"] == "COMPLETED_SUCCESS", (
        "Compute execution must be SUCCESS (exit code 0)"
    )
    assert overnight_run["quality_health"] == "CORRUPTED", (
        "Data quality health must be CORRUPTED despite exit 0"
    )
    assert overnight_run["error_message"] is None
    assert len(overnight_run["run_log"]) == 4

    # Inspect partition freshness
    freshness_resp = test_client.get(f"/api/v1/pipelines/freshness?scenario_id={scenario_id}")
    assert freshness_resp.status_code == 200
    freshness_checks = freshness_resp.json()

    orders_freshness = next(
        (c for c in freshness_checks if c["dataset_name"] == "orders.csv"), None
    )
    assert orders_freshness is not None
    assert orders_freshness["status"] == "STALE"
    assert orders_freshness["hours_behind"] > 0

    # -----------------------------------------------------------------------
    # STAGE 7: Incident Investigation & Safe Report Generation
    # -----------------------------------------------------------------------
    # 1. Synthesize investigation workspace from scenario findings and pipeline logs
    synth_resp = test_client.post(
        "/api/v1/investigations/synthesize",
        json={
            "scenario_id": scenario_id,
            "title": "Incident Investigation: Monday Revenue Spike Anomaly",
        },
    )
    assert synth_resp.status_code == 201, (
        f"Stage 7 investigation synthesis failed: {synth_resp.text}"
    )
    investigation = synth_resp.json()
    investigation_id = investigation["id"]
    assert investigation_id.startswith("inv_")
    assert len(investigation["verified_facts"]) >= 3
    assert len(investigation["hypotheses"]) >= 1
    assert len(investigation["action_items"]) >= 1

    # 2. Generate immutable incident report artifacts
    report_gen_resp = test_client.post(
        "/api/v1/reports/generate",
        json={
            "scenario_id": scenario_id,
            "validation_run_id": val_run_id,
            "investigation_id": investigation_id,
            "title": "Incident Report: Monday Morning Revenue Anomaly",
        },
    )
    assert report_gen_resp.status_code == 201, (
        f"Stage 7 report generation failed: {report_gen_resp.text}"
    )
    report_data = report_gen_resp.json()
    report_id = report_data["report_id"]
    assert report_id.startswith("rep_")

    # Verify physical file persistence
    json_artifact = settings.artifacts_dir / f"{report_id}.json"
    html_artifact = settings.artifacts_dir / f"{report_id}.html"
    assert json_artifact.exists(), f"JSON artifact was not written to {json_artifact}"
    assert html_artifact.exists(), f"HTML artifact was not written to {html_artifact}"

    # 3. Export and assert JSON report artifact
    json_export_resp = test_client.get(f"/api/v1/reports/{report_id}/export?format=json")
    assert json_export_resp.status_code == 200
    assert "application/json" in json_export_resp.headers["content-type"]
    exported_json = json_export_resp.json()
    assert exported_json["report_id"] == report_id
    assert exported_json["scenario"]["id"] == scenario_id
    assert exported_json["validation_summary"]["quality_health"] == "CORRUPTED"
    assert exported_json["validation_summary"]["failed_count"] == 4
    assert exported_json["validation_summary"]["passed_count"] == 4
    assert exported_json["validation_summary"]["total_rules"] == 8
    assert len(exported_json["findings"]) == 8
    failed_report_findings = [f for f in exported_json["findings"] if f["status"] == "FAILED"]
    assert len(failed_report_findings) == 4
    assert len(exported_json["impacted_assets"]) > 0
    assert "sha256" in exported_json["integrity"]

    # 4. Export and assert HTML report artifact with security headers
    html_export_resp = test_client.get(f"/api/v1/reports/{report_id}/export?format=html")
    assert html_export_resp.status_code == 200
    assert "text/html" in html_export_resp.headers["content-type"]

    csp_header = html_export_resp.headers.get("Content-Security-Policy", "")
    assert "default-src 'none'" in csp_header
    assert "style-src 'unsafe-inline'" in csp_header
    assert "sandbox" in csp_header

    html_content = html_export_resp.text
    assert '<meta http-equiv="Content-Security-Policy"' in html_content
    assert "Monday Revenue Mystery" in html_content
    assert "VAL-ORD-001" in html_content
    assert "<script>" not in html_content.lower()  # Disallows unescaped script tags
    assert "<link rel=" not in html_content.lower()  # Completely inlined standalone document

    # -----------------------------------------------------------------------
    # STAGE 8: Verify Recovery with Clean Data & Restore Trust
    # -----------------------------------------------------------------------
    rec_resp = test_client.post(
        "/api/v1/recovery/verify",
        json={"scenario_id": scenario_id},
    )
    assert rec_resp.status_code == 200, f"Stage 8 recovery verification failed: {rec_resp.text}"
    rec_data = rec_resp.json()

    assert rec_data["scenario_id"] == scenario_id
    comparison = rec_data["comparison"]

    # Assert Defective Baseline in diff
    prev_run = comparison["previous_run"]
    assert prev_run["fixture_version"] == "defective"
    assert prev_run["failed_checks"] == 4
    assert prev_run["quality_health"] == "CORRUPTED"

    # Assert Corrected Recovery in diff
    curr_run = comparison["current_run"]
    assert curr_run["fixture_version"] == "corrected"
    assert curr_run["failed_checks"] == 0
    assert curr_run["passed_checks"] == 8
    assert curr_run["quality_health"] == "HEALTHY"

    # Assert all 4 failed checks marked RESOLVED
    resolved = comparison["resolved_findings"]
    assert len(resolved) == 4
    resolved_rules = {r["rule_id"]: r for r in resolved}

    assert resolved_rules["VAL-ORD-001"]["status"] == "RESOLVED"
    assert resolved_rules["VAL-ORD-001"]["previous_status"] == "FAILED"
    assert resolved_rules["VAL-ORD-001"]["current_status"] == "PASSED"

    assert resolved_rules["VAL-ORD-002"]["status"] == "RESOLVED"
    assert resolved_rules["VAL-ORD-002"]["previous_status"] == "FAILED"
    assert resolved_rules["VAL-ORD-002"]["current_status"] == "PASSED"

    assert resolved_rules["VAL-INV-001"]["status"] == "RESOLVED"
    assert resolved_rules["VAL-INV-001"]["previous_status"] == "FAILED"
    assert resolved_rules["VAL-INV-001"]["current_status"] == "PASSED"

    assert resolved_rules["VAL-FRESH-001"]["status"] == "RESOLVED"
    assert resolved_rules["VAL-FRESH-001"]["previous_status"] == "FAILED"
    assert resolved_rules["VAL-FRESH-001"]["current_status"] == "PASSED"

    # Assert downstream recovery status
    assert comparison["downstream_recovery_status"] == "ALL_ASSETS_HEALTHY"

    # Confirm Lineage Graph nodes are all restored to HEALTHY
    lineage_after = test_client.get(f"/api/v1/lineage?scenario_id={scenario_id}").json()
    assert all(n["quality_health"] == "HEALTHY" for n in lineage_after["nodes"])

    # Confirm Freshness is restored to FRESH
    fresh_url = f"/api/v1/pipelines/freshness?scenario_id={scenario_id}"
    freshness_after = test_client.get(fresh_url).json()
    assert all(f["status"] == "FRESH" for f in freshness_after)
    assert all(f["hours_behind"] == 0.0 for f in freshness_after)

    # Confirm scenario active_fixture_version is updated
    scenario_after = test_client.get(f"/api/v1/scenarios/{scenario_id}").json()
    assert scenario_after["active_fixture_version"] == "corrected"

    # Confirm both runs are preserved in historical audit log
    runs_after = test_client.get(f"/api/v1/validations/runs?scenario_id={scenario_id}").json()
    assert len(runs_after) >= 2
    versions = {r["fixture_version"] for r in runs_after}
    assert "defective" in versions
    assert "corrected" in versions


# ===========================================================================
# INDIVIDUAL STAGE ISOLATION TESTS
# ===========================================================================


def test_stage_1_scenario_ingestion_and_dataset_counts(test_client: TestClient) -> None:
    """Stage 1: Verify scenario loading, table population, and exact record counts."""
    resp = test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["scenario_id"] == "monday_revenue_mystery"
    assert data["active_fixture_version"] == "defective"
    assert len(data["loaded_datasets"]) == 4
    assert set(data["loaded_datasets"]) == {"orders", "order_items", "products", "inventory"}
    assert data["rules_registered"] == 8
    assert data["lineage_nodes_loaded"] == 16

    # Verify scenario detail record counts
    detail_resp = test_client.get("/api/v1/scenarios/monday_revenue_mystery")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    counts = {d["id"]: d["record_count"] for d in detail["datasets"]}
    assert counts["orders"] == 1250
    assert counts["order_items"] == 3420
    assert counts["products"] == 250
    assert counts["inventory"] == 250
    assert sum(counts.values()) == 5170


def test_stage_2_quality_validations_execution(test_client: TestClient) -> None:
    """Stage 2: Verify validation engine execution producing exactly 4 failed checks."""
    test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": "monday_revenue_mystery"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "FAILED"
    assert data["total_checks"] == 8
    assert data["passed_checks"] == 4
    assert data["failed_checks"] == 4
    assert data["warning_checks"] == 0
    assert data["skipped_checks"] == 0
    assert data["error_checks"] == 0


def test_stage_3_structured_row_evidence_and_capping(test_client: TestClient) -> None:
    """Stage 3: Verify structured sample keys, row numbers, and sample capping."""
    test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    run_resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": "monday_revenue_mystery"},
    )
    run_id = run_resp.json()["run_id"]

    findings_resp = test_client.get(f"/api/v1/validations/runs/{run_id}/findings")
    assert findings_resp.status_code == 200
    findings_data = findings_resp.json()
    assert findings_data["total_findings"] == 8
    findings = findings_data["items"]

    dup_finding = next(f for f in findings if f["rule_id"] == "VAL-ORD-001")
    assert dup_finding["affected_record_count"] == 15
    assert dup_finding["severity"] == "CRITICAL"
    assert "sample_duplicates" in dup_finding["evidence"]
    assert len(dup_finding["evidence"]["sample_duplicates"]) == 15


def test_stage_4_lineage_dag_integrity_and_traversal(test_client: TestClient) -> None:
    """Stage 4: Verify lineage graph has 16 nodes, 14 edges, is acyclic, and has Dagre coords."""
    test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )

    lineage_resp = test_client.get("/api/v1/lineage?scenario_id=monday_revenue_mystery")
    assert lineage_resp.status_code == 200
    data = lineage_resp.json()

    assert len(data["nodes"]) == 16
    assert len(data["edges"]) == 14

    for node in data["nodes"]:
        assert "x" in node["position"]
        assert "y" in node["position"]

    validate_resp = test_client.post(
        "/api/v1/lineage/validate",
        json={"scenario_id": "monday_revenue_mystery"},
    )
    assert validate_resp.status_code == 200
    vdata = validate_resp.json()
    assert vdata["is_valid"] is True
    assert vdata["is_dag"] is True
    assert len(vdata["cycles"]) == 0


def test_stage_5_downstream_impact_blast_radius_and_isolation(test_client: TestClient) -> None:
    """Stage 5: Verify blast radius reaches report_exec_dash and inventory isolates stock branch."""
    test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": "monday_revenue_mystery"},
    )

    # Orders failure propagates to Executive Dashboard
    orders_resp = test_client.post(
        "/api/v1/impact/trace",
        json={
            "scenario_id": "monday_revenue_mystery",
            "target_type": "DATASET",
            "target_id": "orders.csv",
        },
    )
    assert orders_resp.status_code == 200
    orders_affected = {a["node_id"] for a in orders_resp.json()["affected_assets"]}
    assert "report_exec_dash" in orders_affected
    assert "report_stock_alert" not in orders_affected

    # Inventory failure isolates to Stock Alert
    inv_resp = test_client.post(
        "/api/v1/impact/trace",
        json={
            "scenario_id": "monday_revenue_mystery",
            "target_type": "DATASET",
            "target_id": "inventory.csv",
        },
    )
    assert inv_resp.status_code == 200
    inv_affected = {a["node_id"] for a in inv_resp.json()["affected_assets"]}
    assert "report_stock_alert" in inv_affected
    assert "report_exec_dash" not in inv_affected


def test_stage_6_pipeline_observability_and_dual_dimension(test_client: TestClient) -> None:
    """Stage 6: Verify overnight run has status SUCCESS alongside quality_health CORRUPTED."""
    test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )

    resp = test_client.get("/api/v1/pipelines/runs/pipe_run_20261020_0200")
    assert resp.status_code == 200
    run = resp.json()

    assert run["execution_status"] == "COMPLETED_SUCCESS"
    assert run["quality_health"] == "CORRUPTED"
    assert run["error_message"] is None


def test_stage_7_investigation_and_safe_report_exports(test_client: TestClient) -> None:
    """Stage 7: Verify report generation with JSON and HTML exports and CSP sanitization."""
    test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    val_resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": "monday_revenue_mystery"},
    )
    run_id = val_resp.json()["run_id"]

    gen_resp = test_client.post(
        "/api/v1/reports/generate",
        json={
            "scenario_id": "monday_revenue_mystery",
            "validation_run_id": run_id,
            "title": "Stage 7 Test Report",
        },
    )
    assert gen_resp.status_code == 201
    report_id = gen_resp.json()["report_id"]

    # Export JSON
    json_resp = test_client.get(f"/api/v1/reports/{report_id}/export?format=json")
    assert json_resp.status_code == 200
    assert json_resp.json()["report_id"] == report_id

    # Export HTML
    html_resp = test_client.get(f"/api/v1/reports/{report_id}/export?format=html")
    assert html_resp.status_code == 200
    assert "default-src 'none'" in html_resp.headers.get("Content-Security-Policy", "")
    assert '<meta http-equiv="Content-Security-Policy"' in html_resp.text


def test_stage_8_recovery_verification_and_trust_restoration(test_client: TestClient) -> None:
    """Stage 8: Verify recovery transitions health from CORRUPTED to HEALTHY with 4 RESOLVED."""
    test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": "monday_revenue_mystery"},
    )

    rec_resp = test_client.post(
        "/api/v1/recovery/verify",
        json={"scenario_id": "monday_revenue_mystery"},
    )
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()

    assert rec_data["comparison"]["previous_run"]["failed_checks"] == 4
    assert rec_data["comparison"]["current_run"]["failed_checks"] == 0
    assert rec_data["comparison"]["downstream_recovery_status"] == "ALL_ASSETS_HEALTHY"
    assert len(rec_data["comparison"]["resolved_findings"]) == 4
