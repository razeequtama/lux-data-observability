"""Integration tests for the recovery verification REST API and Monday Revenue Mystery recovery."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def loaded_defective_scenario(client: TestClient) -> str:
    """Load defective Monday Revenue Mystery scenario and run baseline validation."""
    resp = client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    assert resp.status_code == 200, resp.text

    # Execute baseline validation run
    val_resp = client.post(
        "/api/v1/validations/run",
        json={"scenario_id": "monday_revenue_mystery"},
    )
    assert val_resp.status_code == 200, val_resp.text
    assert val_resp.json()["failed_checks"] == 4

    return "monday_revenue_mystery"


def test_recovery_verify_acceptance_criteria(
    client: TestClient,
    loaded_defective_scenario: str,
) -> None:
    """Acceptance Criterion Test:

    1. Re-executing against corrected fixtures yields 0 failed checks.
    2. Comparison diff lists all 4 previously failed checks as RESOLVED.
    3. Quality health transitions to HEALTHY.
    4. Downstream recovery status is ALL_ASSETS_HEALTHY.
    """
    resp = client.post(
        "/api/v1/recovery/verify",
        json={"scenario_id": loaded_defective_scenario},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["scenario_id"] == "monday_revenue_mystery"
    comparison = data["comparison"]

    # 1. Previous run assertions (Defective baseline)
    prev = comparison["previous_run"]
    assert prev["run_id"].startswith("val_run_")
    assert prev["fixture_version"] == "defective"
    assert prev["failed_checks"] == 4
    assert prev["quality_health"] == "CORRUPTED"
    assert prev["total_checks"] == 8
    assert prev["passed_checks"] == 4

    # 2. Current run assertions (Corrected recovery)
    curr = comparison["current_run"]
    assert curr["run_id"].startswith("val_run_")
    assert curr["fixture_version"] == "corrected"
    assert curr["failed_checks"] == 0
    assert curr["quality_health"] == "HEALTHY"
    assert curr["total_checks"] == 8
    assert curr["passed_checks"] == 8

    # 3. Resolved findings checklist assertions (All 4 previously failed checks marked RESOLVED)
    resolved = comparison["resolved_findings"]
    assert len(resolved) == 4

    resolved_map = {item["rule_id"]: item for item in resolved}

    # Defect 1: Order ID uniqueness check
    ord_dup = resolved_map["VAL-ORD-001"]
    assert ord_dup["rule_name"] == "Order ID Uniqueness Check"
    assert ord_dup["status"] == "RESOLVED"
    assert ord_dup["previous_status"] == "FAILED"
    assert ord_dup["current_status"] == "PASSED"

    # Defect 2: Order items referential integrity check
    ord_fk = resolved_map["VAL-ORD-002"]
    assert ord_fk["rule_name"] == "Order Items Foreign Key Check"
    assert ord_fk["status"] == "RESOLVED"
    assert ord_fk["previous_status"] == "FAILED"
    assert ord_fk["current_status"] == "PASSED"

    # Defect 3: Negative inventory check
    inv_range = resolved_map["VAL-INV-001"]
    assert inv_range["rule_name"] == "Inventory Non-Negative Check"
    assert inv_range["status"] == "RESOLVED"
    assert inv_range["previous_status"] == "FAILED"
    assert inv_range["current_status"] == "PASSED"

    # Defect 4: Partition freshness / temporal gap check
    fresh_gap = resolved_map["VAL-FRESH-001"]
    assert fresh_gap["rule_name"] == "Partition Freshness Check"
    assert fresh_gap["status"] == "RESOLVED"
    assert fresh_gap["previous_status"] == "FAILED"
    assert fresh_gap["current_status"] == "PASSED"

    # 4. Downstream recovery status
    assert comparison["downstream_recovery_status"] == "ALL_ASSETS_HEALTHY"


def test_recovery_verify_without_prior_validation_run(
    client: TestClient,
) -> None:
    """Verify recovery verification works cleanly even without running manual validation first."""
    # Load defective scenario without running validation
    load_resp = client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    assert load_resp.status_code == 200

    # Call verify recovery directly
    resp = client.post(
        "/api/v1/recovery/verify",
        json={"scenario_id": "monday_revenue_mystery"},
    )
    assert resp.status_code == 200
    data = resp.json()

    comparison = data["comparison"]
    assert comparison["previous_run"]["failed_checks"] == 4
    assert comparison["previous_run"]["quality_health"] == "CORRUPTED"
    assert comparison["current_run"]["failed_checks"] == 0
    assert comparison["current_run"]["quality_health"] == "HEALTHY"
    assert comparison["downstream_recovery_status"] == "ALL_ASSETS_HEALTHY"


def test_recovery_verify_updates_lineage_and_pipeline_health(
    client: TestClient,
    loaded_defective_scenario: str,
) -> None:
    """Verify that after recovery verification:

    - Lineage nodes all transition to HEALTHY
    - Freshness check transitions to FRESH (0.0h behind)
    - Scenario active_fixture_version becomes 'corrected'
    """
    # 1. Check lineage before recovery: some nodes are CORRUPTED
    lineage_before = client.get(f"/api/v1/lineage?scenario_id={loaded_defective_scenario}").json()
    corrupted_nodes = [n for n in lineage_before["nodes"] if n["quality_health"] == "CORRUPTED"]
    assert len(corrupted_nodes) > 0

    # 2. Trigger recovery verification
    rec_resp = client.post(
        "/api/v1/recovery/verify",
        json={"scenario_id": loaded_defective_scenario},
    )
    assert rec_resp.status_code == 200

    # 3. Check lineage after recovery: all nodes are HEALTHY
    lineage_after = client.get(f"/api/v1/lineage?scenario_id={loaded_defective_scenario}").json()
    assert all(n["quality_health"] == "HEALTHY" for n in lineage_after["nodes"])

    # 4. Check freshness after recovery: orders and inventory are FRESH (0.0h behind)
    freshness_after = client.get(
        f"/api/v1/pipelines/freshness?scenario_id={loaded_defective_scenario}"
    ).json()
    assert all(chk["status"] == "FRESH" for chk in freshness_after)
    assert all(chk["hours_behind"] == 0.0 for chk in freshness_after)

    # 5. Check scenario detail: active_fixture_version is 'corrected'
    scenario_detail = client.get(f"/api/v1/scenarios/{loaded_defective_scenario}").json()
    assert scenario_detail["active_fixture_version"] == "corrected"

    # 6. Check historical runs list: both defective and corrected runs are preserved
    runs_resp = client.get(f"/api/v1/validations/runs?scenario_id={loaded_defective_scenario}")
    assert runs_resp.status_code == 200
    runs = runs_resp.json()
    assert len(runs) >= 2
    versions = {r["fixture_version"] for r in runs}
    assert "defective" in versions
    assert "corrected" in versions


def test_recovery_verify_unknown_scenario(client: TestClient) -> None:
    """Verify 404 response when scenario does not exist."""
    resp = client.post(
        "/api/v1/recovery/verify",
        json={"scenario_id": "non_existent_scenario_xyz"},
    )
    assert resp.status_code == 404
    error = resp.json()["error"]
    assert error["code"] == "SCENARIO_NOT_FOUND"
