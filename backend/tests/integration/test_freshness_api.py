"""Integration tests for Dataset Partition Freshness & SLA Monitoring REST API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.models.dataset import Dataset
from app.models.pipeline import FreshnessCheck
from app.models.scenario import Scenario
from app.services.pipeline.service import parse_iso_datetime


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


def test_get_freshness_empty(test_client: TestClient) -> None:
    """Freshness query for nonexistent scenario returns empty list."""
    resp = test_client.get("/api/v1/pipelines/freshness?scenario_id=nonexistent")
    assert resp.status_code == 200
    assert resp.json() == []


def test_freshness_monday_revenue_mystery_defective_stale(
    test_client: TestClient,
    loaded_defective_scenario: str,
) -> None:
    """
    CRITICAL ACCEPTANCE TEST:
    Verify GET /api/v1/pipelines/freshness identifies orders.csv as STALE (5.99 hours behind SLA).
    """
    resp = test_client.get(f"/api/v1/pipelines/freshness?scenario_id={loaded_defective_scenario}")
    assert resp.status_code == 200
    checks = resp.json()
    assert len(checks) >= 2

    # Verify orders.csv is STALE and 5.99 hours behind SLA
    orders_check = next((c for c in checks if c["dataset_id"] == "orders"), None)
    assert orders_check is not None, "orders freshness check missing"
    assert orders_check["dataset_name"] == "orders.csv"
    assert orders_check["sla_hours"] == 24
    assert orders_check["status"] == "STALE"
    assert orders_check["hours_behind"] == 5.99
    assert orders_check["expected_partition_timestamp"].startswith("2026-10-19T23:59:59")
    assert orders_check["observed_partition_timestamp"].startswith("2026-10-19T18:00:00")

    # Verify inventory.csv is FRESH
    inv_check = next((c for c in checks if c["dataset_id"] == "inventory"), None)
    assert inv_check is not None, "inventory freshness check missing"
    assert inv_check["dataset_name"] == "inventory.csv"
    assert inv_check["sla_hours"] == 6
    assert inv_check["status"] == "FRESH"
    assert inv_check["hours_behind"] == 0.0


def test_freshness_monday_revenue_mystery_corrected_fresh(
    test_client: TestClient,
    loaded_corrected_scenario: str,
) -> None:
    """Verify that in the corrected recovery fixture, orders.csv is FRESH with 0.0 hours behind."""
    resp = test_client.get(f"/api/v1/pipelines/freshness?scenario_id={loaded_corrected_scenario}")
    assert resp.status_code == 200
    checks = resp.json()

    orders_check = next((c for c in checks if c["dataset_id"] == "orders"), None)
    assert orders_check is not None
    assert orders_check["dataset_name"] == "orders.csv"
    assert orders_check["status"] == "FRESH"
    assert orders_check["hours_behind"] == 0.0
    assert orders_check["expected_partition_timestamp"].startswith("2026-10-19T23:59:59")
    assert orders_check["observed_partition_timestamp"].startswith("2026-10-19T23:55:00")


def test_freshness_filter_by_dataset(
    test_client: TestClient,
    loaded_defective_scenario: str,
) -> None:
    """Verify filtering by both scenario_id and dataset_id."""
    resp = test_client.get(
        f"/api/v1/pipelines/freshness?scenario_id={loaded_defective_scenario}&dataset_id=orders"
    )
    assert resp.status_code == 200
    checks = resp.json()
    assert len(checks) == 1
    assert checks[0]["dataset_id"] == "orders"
    assert checks[0]["status"] == "STALE"


def test_freshness_missing_timestamp_edge_case(
    test_client: TestClient,
    db_session: Session,
) -> None:
    """Verify that a missing or null timestamp yields status 'MISSING' with 0.0 hours behind."""
    scenario_id = "sc_edge_missing"
    sc = Scenario(id=scenario_id, name="Missing Timestamp Scenario")
    db_session.add(sc)

    ds = Dataset(
        id="empty_feed",
        scenario_id=scenario_id,
        name="empty_feed.csv",
        file_path="empty_feed.csv",
        file_format="csv",
        file_size_bytes=0,
        record_count=0,
        column_count=0,
        schema_definition="{}",
    )
    db_session.add(ds)

    exp_dt = parse_iso_datetime("2026-10-20T00:00:00Z")
    assert exp_dt is not None
    check = FreshnessCheck(
        id="fresh_missing_check",
        scenario_id=scenario_id,
        dataset_id=ds.id,
        expected_partition_timestamp=exp_dt,
        observed_partition_timestamp=None,
        sla_hours=12,
        status="MISSING",
    )
    db_session.add(check)
    db_session.commit()

    resp = test_client.get(f"/api/v1/pipelines/freshness?scenario_id={scenario_id}")
    assert resp.status_code == 200
    checks = resp.json()
    assert len(checks) == 1
    assert checks[0]["dataset_id"] == "empty_feed"
    assert checks[0]["status"] == "MISSING"
    assert checks[0]["observed_partition_timestamp"] is None
    assert checks[0]["hours_behind"] == 0.0
