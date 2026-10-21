"""Integration tests for Validation Runner Service, persistence, and REST findings API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.services.validation.runner import _cap_evidence_samples


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


@pytest.fixture
def loaded_corrected_scenario(test_client: TestClient) -> str:
    """Load corrected Monday Revenue Mystery scenario into SQLite and return scenario_id."""
    resp = test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "corrected"},
    )
    assert resp.status_code == 200, resp.text
    return "monday_revenue_mystery"


# ---------------------------------------------------------------------------
# 1. Validation Execution on Defective Monday Revenue Mystery Fixtures
# ---------------------------------------------------------------------------


def test_execute_validation_run_defective_fixtures_acceptance(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Acceptance Criterion: Executing validation run produces exactly 4 failed checks."""
    resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": loaded_defective_scenario},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["scenario_id"] == "monday_revenue_mystery"
    assert data["fixture_version"] == "defective"
    assert data["status"] == "FAILED"
    assert data["total_checks"] == 8
    assert data["passed_checks"] == 4
    assert data["failed_checks"] == 4
    assert data["warning_checks"] == 0
    assert data["skipped_checks"] == 0
    assert data["error_checks"] == 0
    assert data["execution_duration_ms"] >= 0
    assert data["run_id"].startswith("val_run_")
    assert "executed_at" in data


def test_get_validation_run_by_id(test_client: TestClient, loaded_defective_scenario: str) -> None:
    """Verify GET /api/v1/validations/runs/{run_id} returns identical run summary."""
    run_resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": loaded_defective_scenario},
    )
    run_id = run_resp.json()["run_id"]

    get_resp = test_client.get(f"/api/v1/validations/runs/{run_id}")
    assert get_resp.status_code == 200
    run_data = get_resp.json()

    assert run_data["run_id"] == run_id
    assert run_data["scenario_id"] == "monday_revenue_mystery"
    assert run_data["status"] == "FAILED"
    assert run_data["total_checks"] == 8
    assert run_data["failed_checks"] == 4
    assert run_data["passed_checks"] == 4


def test_get_validation_run_not_found(test_client: TestClient) -> None:
    """Verify GET /api/v1/validations/runs/{run_id} returns 404 for unknown run."""
    resp = test_client.get("/api/v1/validations/runs/val_run_unknown_999")
    assert resp.status_code == 404
    error = resp.json()["error"]
    assert error["code"] == "VALIDATION_RUN_NOT_FOUND"
    assert "val_run_unknown_999" in error["message"]


# ---------------------------------------------------------------------------
# 2. Granular Findings & Structured Evidence Assertions
# ---------------------------------------------------------------------------


def test_findings_structured_evidence_defects(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Acceptance Criterion: Findings contain sample duplicates and broken foreign keys."""
    run_resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": loaded_defective_scenario},
    )
    run_id = run_resp.json()["run_id"]

    # Retrieve all findings
    resp = test_client.get(f"/api/v1/validations/runs/{run_id}/findings")
    assert resp.status_code == 200
    data = resp.json()

    assert data["run_id"] == run_id
    assert data["total_findings"] == 8
    assert len(data["items"]) == 8

    # Filter findings by rule ID
    findings_by_rule = {item["rule_id"]: item for item in data["items"]}

    # Defect 1: VAL-ORD-001 - Order ID Uniqueness Check (orders.csv)
    ord_finding = findings_by_rule["VAL-ORD-001"]
    assert ord_finding["status"] == "FAILED"
    assert ord_finding["severity"] == "CRITICAL"
    assert ord_finding["dataset_id"] == "orders"
    assert ord_finding["affected_fields"] == ["order_id"]
    assert ord_finding["affected_record_count"] == 15
    assert ord_finding["total_record_count"] == 1250
    assert "sample_duplicates" in ord_finding["evidence"]
    sample_dups = ord_finding["evidence"]["sample_duplicates"]
    assert len(sample_dups) == 15
    # Verify duplicates contain order_id and row indices
    first_dup = sample_dups[0]
    assert "order_id" in first_dup
    assert "occurrences" in first_dup
    assert len(first_dup["row_indices"]) >= 2

    # Defect 2: VAL-ORD-002 - Order Items Referential Integrity (order_items.csv)
    item_finding = findings_by_rule["VAL-ORD-002"]
    assert item_finding["status"] == "FAILED"
    assert item_finding["severity"] == "HIGH"
    assert item_finding["dataset_id"] == "order_items"
    assert item_finding["affected_fields"] == ["product_id"]
    assert item_finding["affected_record_count"] == 24
    assert item_finding["total_record_count"] == 3420
    assert "sample_orphaned_keys" in item_finding["evidence"]
    orphaned_keys = item_finding["evidence"]["sample_orphaned_keys"]
    assert len(orphaned_keys) == 24
    assert "PRD-9001" in orphaned_keys
    assert "sample_violations" in item_finding["evidence"]

    # Defect 3: VAL-INV-001 - Inventory Non-Negative Check (inventory.csv)
    inv_finding = findings_by_rule["VAL-INV-001"]
    assert inv_finding["status"] == "FAILED"
    assert inv_finding["severity"] == "HIGH"
    assert inv_finding["dataset_id"] == "inventory"
    assert inv_finding["affected_fields"] == ["quantity_on_hand"]
    assert inv_finding["affected_record_count"] == 8
    assert inv_finding["total_record_count"] == 250

    # Defect 4: VAL-FRESH-001 - Freshness Sunday Gap (orders.csv)
    fresh_finding = findings_by_rule["VAL-FRESH-001"]
    assert fresh_finding["status"] == "FAILED"
    assert fresh_finding["severity"] == "MEDIUM"
    assert fresh_finding["dataset_id"] == "orders"
    assert fresh_finding["affected_record_count"] == 1
    assert "max_gap_hours" in fresh_finding["evidence"]

    # Passed Rules
    passed_rules = ["VAL-ORD-003", "VAL-PRD-001", "VAL-PRD-002", "VAL-INV-002"]
    for p_rule_id in passed_rules:
        p_finding = findings_by_rule[p_rule_id]
        assert p_finding["status"] == "PASSED"
        assert p_finding["affected_record_count"] == 0


# ---------------------------------------------------------------------------
# 3. Filtering and Pagination on Findings
# ---------------------------------------------------------------------------


def test_findings_filtering_by_status(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Verify filtering findings by status=FAILED and status=PASSED."""
    run_resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": loaded_defective_scenario},
    )
    run_id = run_resp.json()["run_id"]

    # Filter status=FAILED
    failed_resp = test_client.get(f"/api/v1/validations/runs/{run_id}/findings?status=FAILED")
    assert failed_resp.status_code == 200
    failed_data = failed_resp.json()
    assert failed_data["total_findings"] == 4
    assert len(failed_data["items"]) == 4
    assert all(item["status"] == "FAILED" for item in failed_data["items"])

    # Filter status=PASSED
    passed_resp = test_client.get(f"/api/v1/validations/runs/{run_id}/findings?status=PASSED")
    assert passed_resp.status_code == 200
    passed_data = passed_resp.json()
    assert passed_data["total_findings"] == 4
    assert len(passed_data["items"]) == 4
    assert all(item["status"] == "PASSED" for item in passed_data["items"])


def test_findings_filtering_by_severity(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Verify filtering findings by severity=CRITICAL."""
    run_resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": loaded_defective_scenario},
    )
    run_id = run_resp.json()["run_id"]

    crit_resp = test_client.get(f"/api/v1/validations/runs/{run_id}/findings?severity=CRITICAL")
    assert crit_resp.status_code == 200
    crit_data = crit_resp.json()

    # 4 rules in Monday Revenue Mystery have severity=CRITICAL:
    # VAL-ORD-001, VAL-ORD-003, VAL-PRD-001, VAL-INV-002
    assert crit_data["total_findings"] == 4
    assert all(item["severity"] == "CRITICAL" for item in crit_data["items"])

    # Combined filter: severity=CRITICAL & status=FAILED
    crit_failed_resp = test_client.get(
        f"/api/v1/validations/runs/{run_id}/findings?severity=CRITICAL&status=FAILED"
    )
    assert crit_failed_resp.status_code == 200
    cf_data = crit_failed_resp.json()
    assert cf_data["total_findings"] == 1
    assert cf_data["items"][0]["rule_id"] == "VAL-ORD-001"


def test_findings_filtering_by_dataset_id(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Verify filtering findings by dataset_id=orders."""
    run_resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": loaded_defective_scenario},
    )
    run_id = run_resp.json()["run_id"]

    ds_resp = test_client.get(f"/api/v1/validations/runs/{run_id}/findings?dataset_id=orders")
    assert ds_resp.status_code == 200
    ds_data = ds_resp.json()

    # orders has 3 rules: VAL-ORD-001, VAL-ORD-003, VAL-FRESH-001
    assert ds_data["total_findings"] == 3
    assert all(item["dataset_id"] == "orders" for item in ds_data["items"])


def test_findings_pagination(test_client: TestClient, loaded_defective_scenario: str) -> None:
    """Verify pagination with limit and offset."""
    run_resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": loaded_defective_scenario},
    )
    run_id = run_resp.json()["run_id"]

    # Page 1: limit 3, offset 0
    page1 = test_client.get(f"/api/v1/validations/runs/{run_id}/findings?limit=3&offset=0").json()
    assert page1["total_findings"] == 8
    assert len(page1["items"]) == 3

    # Page 2: limit 3, offset 3
    page2 = test_client.get(f"/api/v1/validations/runs/{run_id}/findings?limit=3&offset=3").json()
    assert page2["total_findings"] == 8
    assert len(page2["items"]) == 3

    # Page 3: limit 3, offset 6
    page3 = test_client.get(f"/api/v1/validations/runs/{run_id}/findings?limit=3&offset=6").json()
    assert page3["total_findings"] == 8
    assert len(page3["items"]) == 2

    # Assert disjunction of IDs across pages
    page1_ids = {item["id"] for item in page1["items"]}
    page2_ids = {item["id"] for item in page2["items"]}
    page3_ids = {item["id"] for item in page3["items"]}

    assert len(page1_ids.intersection(page2_ids)) == 0
    assert len(page2_ids.intersection(page3_ids)) == 0
    assert len(page1_ids.union(page2_ids).union(page3_ids)) == 8


# ---------------------------------------------------------------------------
# 4. Partial Dataset Execution & Corrected Recovery Execution
# ---------------------------------------------------------------------------


def test_execute_partial_dataset_run(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Verify executing validation on a subset of datasets (inventory only)."""
    resp = test_client.post(
        "/api/v1/validations/run",
        json={
            "scenario_id": loaded_defective_scenario,
            "dataset_ids": ["inventory"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_checks"] == 2
    assert data["failed_checks"] == 1  # VAL-INV-001 failed
    assert data["passed_checks"] == 1  # VAL-INV-002 passed
    assert data["status"] == "FAILED"


def test_execute_validation_run_corrected_fixtures(
    test_client: TestClient, loaded_corrected_scenario: str
) -> None:
    """Verify executing validation on corrected fixtures produces 0 failures."""
    resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": loaded_corrected_scenario},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["scenario_id"] == "monday_revenue_mystery"
    assert data["fixture_version"] == "corrected"
    assert data["status"] == "PASSED"
    assert data["total_checks"] == 8
    assert data["passed_checks"] == 8
    assert data["failed_checks"] == 0
    assert data["warning_checks"] == 0
    assert data["error_checks"] == 0


def test_list_historical_validation_runs(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Verify GET /api/v1/validations/runs lists runs chronologically."""
    # Run 1
    resp1 = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": loaded_defective_scenario},
    )
    run1_id = resp1.json()["run_id"]

    # Run 2
    resp2 = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": loaded_defective_scenario},
    )
    run2_id = resp2.json()["run_id"]

    list_resp = test_client.get(f"/api/v1/validations/runs?scenario_id={loaded_defective_scenario}")
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert len(runs) >= 2
    run_ids = [r["run_id"] for r in runs]
    assert run1_id in run_ids
    assert run2_id in run_ids


# ---------------------------------------------------------------------------
# 5. Error Handling and Edge Cases
# ---------------------------------------------------------------------------


def test_execute_validation_run_unknown_scenario(test_client: TestClient) -> None:
    """Verify 404 error when running validations on non-existent scenario."""
    resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": "non_existent_scenario_123"},
    )
    assert resp.status_code == 404
    error = resp.json()["error"]
    assert error["code"] == "SCENARIO_NOT_FOUND"


def test_execute_validation_run_unknown_dataset(
    test_client: TestClient, loaded_defective_scenario: str
) -> None:
    """Verify 404 error when dataset_ids contains non-existent dataset."""
    resp = test_client.post(
        "/api/v1/validations/run",
        json={
            "scenario_id": loaded_defective_scenario,
            "dataset_ids": ["orders", "phantom_dataset"],
        },
    )
    assert resp.status_code == 404
    error = resp.json()["error"]
    assert error["code"] == "DATASET_NOT_FOUND"
    assert "phantom_dataset" in error["message"]


def test_cap_evidence_samples_bounds_large_arrays() -> None:
    """Edge Case: Ensure large error sample sets are capped at 50 items."""
    large_sample = [{"idx": i, "val": f"val_{i}"} for i in range(120)]
    evidence = {
        "rule": "SAMPLE_TEST",
        "sample_duplicates": large_sample,
        "nested": {"sample_rows": list(range(75))},
    }

    capped = _cap_evidence_samples(evidence, max_samples=50)

    assert len(capped["sample_duplicates"]) == 50
    assert capped["sample_duplicates_truncated"] is True
    assert capped["sample_duplicates_total_count"] == 120

    assert len(capped["nested"]["sample_rows"]) == 50
    assert capped["nested"]["sample_rows_truncated"] is True
    assert capped["nested"]["sample_rows_total_count"] == 75
