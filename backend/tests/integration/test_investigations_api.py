"""Integration tests for Investigation Workspace REST API endpoints."""

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
def loaded_scenario(test_client: TestClient) -> str:
    """Load defective Monday Revenue Mystery scenario and return scenario ID."""
    resp = test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    assert resp.status_code == 200, resp.text
    return "monday_revenue_mystery"


def test_create_investigation_api_success(test_client: TestClient, loaded_scenario: str) -> None:
    """POST /api/v1/investigations creates investigation workspace and returns 201 Created."""
    payload = {
        "scenario_id": loaded_scenario,
        "title": "Investigation: Monday Morning Revenue Anomaly",
        "status": "OPEN",
        "verified_facts": [
            "Overnight ETL pipeline succeeded at 02:08 UTC with exit code 0.",
            "15 duplicate order IDs detected in orders.csv.",
            "24 orphaned order items detected referencing invalid product IDs.",
            "Downstream Executive Dashboard is potentially compromised.",
        ],
        "hypotheses": [
            "Upstream webhook duplicate delivery during Sunday night retry storm.",
            "Product catalog sync failed before order line items were ingested.",
        ],
        "action_items": [
            "Deduplicate orders.csv using idempotent order UUID check.",
            "Backfill missing products.csv catalog rows.",
            "Re-execute daily revenue aggregation and verify metric recovery.",
        ],
    }

    resp = test_client.post("/api/v1/investigations", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["id"].startswith("inv_")
    assert data["scenario_id"] == loaded_scenario
    assert data["title"] == payload["title"]
    assert data["status"] == "OPEN"
    assert len(data["verified_facts"]) == 4
    assert len(data["hypotheses"]) == 2
    assert len(data["action_items"]) == 3
    assert data["verified_facts"][0] == payload["verified_facts"][0]
    assert data["hypotheses"][0] == payload["hypotheses"][0]
    assert data["action_items"][0] == payload["action_items"][0]
    assert "created_at" in data
    assert "updated_at" in data


def test_create_investigation_empty_action_items(
    test_client: TestClient, loaded_scenario: str
) -> None:
    """Edge Case: Empty action items list is handled cleanly with 201 Created and [] returned."""
    payload = {
        "scenario_id": loaded_scenario,
        "title": "Investigation with Empty Actions",
        "verified_facts": ["Fact 1"],
        "hypotheses": ["Hypothesis 1"],
        "action_items": [],
    }

    resp = test_client.post("/api/v1/investigations", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["action_items"] == []


def test_create_investigation_invalid_scenario_returns_404(test_client: TestClient) -> None:
    """Creating an investigation for a non-existent scenario returns 404 with error envelope."""
    payload = {
        "scenario_id": "nonexistent_scenario",
        "title": "Invalid Investigation",
        "verified_facts": [],
        "hypotheses": [],
        "action_items": [],
    }

    resp = test_client.post("/api/v1/investigations", json=payload)
    assert resp.status_code == 404
    error = resp.json()["error"]
    assert error["code"] == "SCENARIO_NOT_FOUND"


def test_get_investigation_by_id_success(test_client: TestClient, loaded_scenario: str) -> None:
    """GET /api/v1/investigations/{id} returns full investigation representation."""
    create_resp = test_client.post(
        "/api/v1/investigations",
        json={
            "scenario_id": loaded_scenario,
            "title": "Get by ID Test",
            "verified_facts": ["Fact A", "Fact B"],
            "hypotheses": ["Hypo A"],
            "action_items": ["Action A"],
        },
    )
    inv_id = create_resp.json()["id"]

    resp = test_client.get(f"/api/v1/investigations/{inv_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == inv_id
    assert data["verified_facts"] == ["Fact A", "Fact B"]
    assert data["hypotheses"] == ["Hypo A"]
    assert data["action_items"] == ["Action A"]


def test_get_investigation_nonexistent_returns_404(test_client: TestClient) -> None:
    """GET /api/v1/investigations/{id} returns 404 for unknown ID."""
    resp = test_client.get("/api/v1/investigations/inv_99999999")
    assert resp.status_code == 404
    error = resp.json()["error"]
    assert error["code"] == "INVESTIGATION_NOT_FOUND"


def test_list_investigations_and_filter(test_client: TestClient, loaded_scenario: str) -> None:
    """GET /api/v1/investigations lists workspaces with optional scenario and status filter."""
    test_client.post(
        "/api/v1/investigations",
        json={
            "scenario_id": loaded_scenario,
            "title": "List Test 1",
            "status": "OPEN",
        },
    )
    test_client.post(
        "/api/v1/investigations",
        json={
            "scenario_id": loaded_scenario,
            "title": "List Test 2",
            "status": "RESOLVED",
        },
    )

    # List all for scenario
    resp = test_client.get(f"/api/v1/investigations?scenario_id={loaded_scenario}")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 2

    # Filter by status
    resolved_resp = test_client.get(
        f"/api/v1/investigations?scenario_id={loaded_scenario}&status=RESOLVED"
    )
    assert resolved_resp.status_code == 200
    resolved_items = resolved_resp.json()
    assert all(item["status"] == "RESOLVED" for item in resolved_items)


def test_update_investigation_api(test_client: TestClient, loaded_scenario: str) -> None:
    """PATCH /api/v1/investigations/{id} updates workspace fields."""
    create_resp = test_client.post(
        "/api/v1/investigations",
        json={
            "scenario_id": loaded_scenario,
            "title": "Original Title",
            "status": "OPEN",
            "verified_facts": ["Original Fact"],
            "hypotheses": ["Original Hypothesis"],
            "action_items": [],
        },
    )
    inv_id = create_resp.json()["id"]

    patch_resp = test_client.patch(
        f"/api/v1/investigations/{inv_id}",
        json={
            "title": "Refined Title",
            "status": "INVESTIGATING",
            "action_items": ["Deploy fix"],
        },
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["title"] == "Refined Title"
    assert data["status"] == "INVESTIGATING"
    assert data["verified_facts"] == ["Original Fact"]  # preserved
    assert data["action_items"] == ["Deploy fix"]


def test_delete_investigation_api(test_client: TestClient, loaded_scenario: str) -> None:
    """DELETE /api/v1/investigations/{id} removes investigation and returns 204."""
    create_resp = test_client.post(
        "/api/v1/investigations",
        json={
            "scenario_id": loaded_scenario,
            "title": "To Delete API",
        },
    )
    inv_id = create_resp.json()["id"]

    del_resp = test_client.delete(f"/api/v1/investigations/{inv_id}")
    assert del_resp.status_code == 204

    get_resp = test_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_resp.status_code == 404


def test_synthesize_investigation_api(test_client: TestClient, loaded_scenario: str) -> None:
    """POST /api/v1/investigations/synthesize auto-assembles workspace from findings and runs."""
    # Run validations first to produce findings
    val_resp = test_client.post("/api/v1/validations/run", json={"scenario_id": loaded_scenario})
    assert val_resp.status_code == 200

    synth_resp = test_client.post(
        "/api/v1/investigations/synthesize",
        json={"scenario_id": loaded_scenario},
    )
    assert synth_resp.status_code == 201, synth_resp.text
    data = synth_resp.json()

    assert data["id"].startswith("inv_")
    assert data["scenario_id"] == loaded_scenario
    assert len(data["verified_facts"]) >= 2
    assert len(data["hypotheses"]) >= 1
    assert len(data["action_items"]) >= 1
    # Check that pipeline execution success and data corruption are acknowledged in verified facts
    facts_text = " ".join(data["verified_facts"])
    assert "pipeline" in facts_text.lower() or "rule" in facts_text.lower()
