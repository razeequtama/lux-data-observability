"""Integration tests for Pipeline Run History API and dual-dimension status tracking."""

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


@pytest.fixture
def loaded_corrected_scenario(test_client: TestClient) -> str:
    """Load corrected Monday Revenue Mystery scenario into SQLite and return scenario_id."""
    resp = test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "corrected"},
    )
    assert resp.status_code == 200, resp.text
    return "monday_revenue_mystery"


def test_list_pipeline_runs_empty(test_client: TestClient) -> None:
    """Listing pipeline runs for non-existent scenario returns empty list."""
    resp = test_client.get("/api/v1/pipelines/runs?scenario_id=nonexistent")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_pipeline_runs_monday_revenue_mystery(
    test_client: TestClient,
    loaded_defective_scenario: str,
) -> None:
    """Verify listing historical runs returns chronological sequence with step logs."""
    resp = test_client.get(f"/api/v1/pipelines/runs?scenario_id={loaded_defective_scenario}")
    assert resp.status_code == 200
    runs = resp.json()
    assert len(runs) == 3

    # Ordered descending by start_time (latest first)
    run_ids = [r["id"] for r in runs]
    assert run_ids == [
        "pipe_run_20261020_0200",
        "pipe_run_20261019_0200",
        "pipe_run_20261018_0200",
    ]

    for run in runs:
        assert run["scenario_id"] == "monday_revenue_mystery"
        assert run["pipeline_name"] == "nightly_ecommerce_etl"
        assert run["duration_ms"] > 0
        assert run["records_ingested"] > 0
        assert run["records_written"] > 0
        assert isinstance(run["run_log"], list)
        assert len(run["run_log"]) == 4


def test_dual_dimension_overnight_run_success_vs_corrupted(
    test_client: TestClient,
    loaded_defective_scenario: str,
) -> None:
    """
    CRITICAL ACCEPTANCE TEST:
    Verify that the overnight run demonstrates:
    Compute Execution Status = 'COMPLETED_SUCCESS' (exit code 0)
    Data Quality Health = 'CORRUPTED' (broken data)
    """
    resp = test_client.get("/api/v1/pipelines/runs/pipe_run_20261020_0200")
    assert resp.status_code == 200
    run = resp.json()

    assert run["id"] == "pipe_run_20261020_0200"
    assert run["scenario_id"] == "monday_revenue_mystery"
    assert run["pipeline_name"] == "nightly_ecommerce_etl"

    # Execution Succeeded (Exit 0)
    assert run["execution_status"] == "COMPLETED_SUCCESS"
    assert run["error_message"] is None

    # But Data Quality Health is Corrupted!
    assert run["quality_health"] == "CORRUPTED"

    # Metrics & Duration
    assert run["duration_ms"] == 494000
    assert run["records_ingested"] == 4670
    assert run["records_written"] == 4655

    # Step Logs
    steps = run["run_log"]
    assert len(steps) == 4
    step_names = [s["step"] for s in steps]
    assert step_names == [
        "extract_sources",
        "transform_clean_orders",
        "transform_order_line_items",
        "aggregate_daily_revenue",
    ]
    assert all(s["status"] == "SUCCESS" for s in steps)


def test_previous_runs_healthy(
    test_client: TestClient,
    loaded_defective_scenario: str,
) -> None:
    """Verify that prior days (Sunday & Saturday) had HEALTHY quality status."""
    resp18 = test_client.get("/api/v1/pipelines/runs/pipe_run_20261018_0200")
    assert resp18.status_code == 200
    assert resp18.json()["execution_status"] == "COMPLETED_SUCCESS"
    assert resp18.json()["quality_health"] == "HEALTHY"

    resp19 = test_client.get("/api/v1/pipelines/runs/pipe_run_20261019_0200")
    assert resp19.status_code == 200
    assert resp19.json()["execution_status"] == "COMPLETED_SUCCESS"
    assert resp19.json()["quality_health"] == "HEALTHY"


def test_get_pipeline_run_not_found(test_client: TestClient) -> None:
    """Verify 404 response when querying a non-existent pipeline run ID."""
    resp = test_client.get("/api/v1/pipelines/runs/pipe_nonexistent_999")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "PIPELINE_RUN_NOT_FOUND"


def test_pipeline_runs_pagination(
    test_client: TestClient,
    loaded_defective_scenario: str,
) -> None:
    """Verify limit and offset pagination on pipeline runs listing."""
    resp_limit = test_client.get(
        f"/api/v1/pipelines/runs?scenario_id={loaded_defective_scenario}&limit=2"
    )
    assert resp_limit.status_code == 200
    runs = resp_limit.json()
    assert len(runs) == 2
    assert runs[0]["id"] == "pipe_run_20261020_0200"
    assert runs[1]["id"] == "pipe_run_20261019_0200"

    resp_offset = test_client.get(
        f"/api/v1/pipelines/runs?scenario_id={loaded_defective_scenario}&limit=2&offset=2"
    )
    assert resp_offset.status_code == 200
    runs_offset = resp_offset.json()
    assert len(runs_offset) == 1
    assert runs_offset[0]["id"] == "pipe_run_20261018_0200"


def test_pipeline_runs_include_logs_flag(
    test_client: TestClient,
    loaded_defective_scenario: str,
) -> None:
    """Verify include_logs=false suppresses step execution logs for lightweight listing."""
    resp = test_client.get(
        f"/api/v1/pipelines/runs?scenario_id={loaded_defective_scenario}&include_logs=false"
    )
    assert resp.status_code == 200
    runs = resp.json()
    assert len(runs) == 3
    for run in runs:
        assert run["run_log"] == []


def test_corrected_scenario_pipeline_runs(
    test_client: TestClient,
    loaded_corrected_scenario: str,
) -> None:
    """Verify that loading the corrected fixture version marks the run as HEALTHY."""
    resp = test_client.get("/api/v1/pipelines/runs/pipe_run_20261020_0200")
    assert resp.status_code == 200
    run = resp.json()
    assert run["execution_status"] == "COMPLETED_SUCCESS"
    assert run["quality_health"] == "HEALTHY"
