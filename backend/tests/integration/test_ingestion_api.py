"""Integration tests for Dataset Ingestion, Scenario Loader, and Upload Security Service."""

import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
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


def test_list_scenarios_returns_bundled_scenarios(test_client: TestClient) -> None:
    """Verify GET /api/v1/scenarios discovers bundled Monday Revenue Mystery."""
    response = test_client.get("/api/v1/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    scenario = next((s for s in data if s["id"] == "monday_revenue_mystery"), None)
    assert scenario is not None
    assert scenario["name"] == "Monday Revenue Mystery"
    assert scenario["is_bundled"] is True
    assert scenario["dataset_count"] == 4
    assert scenario["rule_count"] == 8


def test_load_scenario_acceptance_criteria(test_client: TestClient) -> None:
    """Verify loading Monday Revenue Mystery populates SQLite and returns HTTP 200."""
    response = test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["scenario_id"] == "monday_revenue_mystery"
    assert data["active_fixture_version"] == "defective"
    assert set(data["loaded_datasets"]) == {"orders", "order_items", "products", "inventory"}
    assert data["rules_registered"] == 8
    assert data["lineage_nodes_loaded"] == 16
    assert "Monday Revenue Mystery" in data["message"]


def test_get_scenario_detail_after_loading(test_client: TestClient) -> None:
    """Verify GET /api/v1/scenarios/{id} returns full metadata and dataset descriptors."""
    test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )

    response = test_client.get("/api/v1/scenarios/monday_revenue_mystery")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == "monday_revenue_mystery"
    assert data["active_fixture_version"] == "defective"
    assert data["dataset_count"] == 4
    assert data["rule_count"] == 8
    assert len(data["datasets"]) == 4


def test_list_datasets_and_counts(test_client: TestClient) -> None:
    """Verify GET /api/v1/datasets returns accurate dataset record counts."""
    test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )

    response = test_client.get("/api/v1/datasets?scenario_id=monday_revenue_mystery")
    assert response.status_code == 200
    datasets = {d["id"]: d for d in response.json()}

    assert "orders" in datasets
    assert datasets["orders"]["record_count"] == 1250
    assert datasets["orders"]["column_count"] == 5

    assert "order_items" in datasets
    assert datasets["order_items"]["record_count"] == 3420

    assert "products" in datasets
    assert datasets["products"]["record_count"] == 250

    assert "inventory" in datasets
    assert datasets["inventory"]["record_count"] == 250


def test_dataset_preview_acceptance_criteria(test_client: TestClient) -> None:
    """Verify GET /api/v1/datasets/orders/preview?limit=10 returns exact preview rows."""
    test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )

    response = test_client.get("/api/v1/datasets/orders/preview?limit=10")
    assert response.status_code == 200
    data = response.json()

    assert data["dataset_id"] == "orders"
    assert data["total_records"] == 1250
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert data["columns"] == [
        "order_id",
        "customer_id",
        "order_date",
        "order_status",
        "total_amount",
    ]
    assert len(data["rows"]) == 10

    # Verify first row matches expected structure and types
    first_row = data["rows"][0]
    assert first_row["order_id"] == "ORD-0001"
    assert "customer_id" in first_row
    assert "order_date" in first_row
    assert isinstance(first_row["total_amount"], (int, float))


def test_dataset_preview_pagination(test_client: TestClient) -> None:
    """Verify preview pagination with offset and limit."""
    test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )

    page1 = test_client.get("/api/v1/datasets/orders/preview?limit=5&offset=0").json()
    page2 = test_client.get("/api/v1/datasets/orders/preview?limit=5&offset=5").json()

    assert len(page1["rows"]) == 5
    assert len(page2["rows"]) == 5
    assert page1["offset"] == 0
    assert page2["offset"] == 5

    page1_ids = [r["order_id"] for r in page1["rows"]]
    page2_ids = [r["order_id"] for r in page2["rows"]]
    assert set(page1_ids).isdisjoint(set(page2_ids))


def test_dataset_preview_upper_limit_enforced(test_client: TestClient) -> None:
    """Verify preview endpoint enforces maximum limit of 100."""
    test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )

    response = test_client.get("/api/v1/datasets/orders/preview?limit=200")
    # Query parameter le=100 returns 422 Unprocessable Entity
    assert response.status_code == 422


def test_dataset_preview_not_found(test_client: TestClient) -> None:
    """Verify 404 with error envelope when dataset does not exist."""
    response = test_client.get("/api/v1/datasets/unknown_dataset_xyz/preview")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "DATASET_NOT_FOUND"


def test_upload_security_oversized_file_rejected_acceptance_criteria(
    test_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify uploads > 20MB return HTTP 413 Payload Too Large."""
    # Temporarily set max upload limit to 100 KB for fast deterministic testing
    monkeypatch.setattr(settings, "max_upload_size_bytes", 100 * 1024)

    oversized_content = b"order_id,amount\n" + (b"ORD-1,10.0\n" * 10000)  # ~110 KB
    response = test_client.post(
        "/api/v1/datasets/upload",
        files={"file": ("large_orders.csv", io.BytesIO(oversized_content), "text/csv")},
    )
    assert response.status_code == 413
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_upload_security_path_traversal_payloads_acceptance_criteria(
    test_client: TestClient,
) -> None:
    """Verify path traversal payloads in filename return HTTP 400."""
    traversal_filenames = [
        "../../etc/passwd.csv",
        "..\\windows\\system32\\cmd.csv",
        "safe_prefix/../../evil.csv",
        "orders.csv\x00.exe",
        "....//....//etc/shadow.csv",
    ]

    for malicious_name in traversal_filenames:
        response = test_client.post(
            "/api/v1/datasets/upload",
            files={"file": (malicious_name, io.BytesIO(b"col1,col2\n1,2\n"), "text/csv")},
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "PATH_TRAVERSAL_DETECTED"


def test_upload_security_disallowed_extension_rejected(test_client: TestClient) -> None:
    """Verify non-whitelisted extensions are rejected with HTTP 400."""
    disallowed_filenames = [
        "malware.exe",
        "backdoor.py",
        "script.sh",
        "index.html",
        "exploit.bat",
    ]

    for disallowed_name in disallowed_filenames:
        response = test_client.post(
            "/api/v1/datasets/upload",
            files={"file": (disallowed_name, io.BytesIO(b"print('hello')\n"), "text/plain")},
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_upload_valid_csv_and_preview(test_client: TestClient) -> None:
    """Verify uploading a clean CSV file succeeds with 201 Created and can be previewed."""
    csv_content = b"transaction_id,amount,status\nTXN-01,100.50,SUCCESS\nTXN-02,250.00,PENDING\n"
    response = test_client.post(
        "/api/v1/datasets/upload",
        files={"file": ("custom_txns.csv", io.BytesIO(csv_content), "text/csv")},
        data={"dataset_name": "Custom Transactions"},
    )
    assert response.status_code == 201
    upload_data = response.json()

    assert upload_data["name"] == "Custom Transactions"
    assert upload_data["format"] == "csv"
    assert upload_data["record_count"] == 2
    assert upload_data["column_count"] == 3

    dataset_id = upload_data["dataset_id"]

    # Preview the uploaded dataset
    preview_resp = test_client.get(f"/api/v1/datasets/{dataset_id}/preview")
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    assert preview_data["total_records"] == 2
    assert preview_data["columns"] == ["transaction_id", "amount", "status"]
    assert len(preview_data["rows"]) == 2
    assert preview_data["rows"][0]["transaction_id"] == "TXN-01"
    assert preview_data["rows"][0]["amount"] == 100.50


def test_upload_valid_json_and_preview(test_client: TestClient) -> None:
    """Verify uploading a clean JSON file succeeds with 201 Created and can be previewed."""
    json_content = b'[{"event_id": "EVT-1", "user_id": 10}, {"event_id": "EVT-2", "user_id": 20}]'
    response = test_client.post(
        "/api/v1/datasets/upload",
        files={"file": ("events.json", io.BytesIO(json_content), "application/json")},
    )
    assert response.status_code == 201
    upload_data = response.json()

    assert upload_data["name"] == "events.json"
    assert upload_data["format"] == "json"
    assert upload_data["record_count"] == 2
    assert upload_data["column_count"] == 2

    dataset_id = upload_data["dataset_id"]
    preview_resp = test_client.get(f"/api/v1/datasets/{dataset_id}/preview")
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    assert preview_data["total_records"] == 2
    assert preview_data["rows"][0]["event_id"] == "EVT-1"


def test_reload_scenario_with_corrected_fixtures(test_client: TestClient) -> None:
    """Verify reloading scenario with corrected fixtures updates version cleanly."""
    # 1. Load defective first
    res1 = test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    assert res1.status_code == 200
    assert res1.json()["active_fixture_version"] == "defective"

    # 2. Reload with corrected fixtures
    res2 = test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "corrected"},
    )
    assert res2.status_code == 200
    assert res2.json()["active_fixture_version"] == "corrected"

    # 3. Verify scenario detail reports corrected version
    detail = test_client.get("/api/v1/scenarios/monday_revenue_mystery").json()
    assert detail["active_fixture_version"] == "corrected"


def test_unload_scenario_preserves_csv_fixtures(test_client: TestClient) -> None:
    """Verify unloading clears SQLite while preserving all .csv fixture files untouched."""
    # 1. Load scenario first
    load_res = test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    assert load_res.status_code == 200

    # Verify datasets are loaded into SQLite
    list_res = test_client.get("/api/v1/datasets?scenario_id=monday_revenue_mystery")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 4

    # Capture fixture files snapshot before unload
    fixtures_dir = settings.scenarios_dir / "monday_revenue_mystery" / "defective"
    csv_files = list(fixtures_dir.glob("*.csv"))
    assert len(csv_files) >= 4
    csv_snapshots = {f.name: (f.stat().st_size, f.read_bytes()) for f in csv_files}

    # 2. Call unload scenario endpoint
    unload_res = test_client.post("/api/v1/scenarios/monday_revenue_mystery/unload")
    assert unload_res.status_code == 200
    unload_data = unload_res.json()

    assert unload_data["scenario_id"] == "monday_revenue_mystery"
    assert set(unload_data["unloaded_datasets"]) == {
        "orders",
        "order_items",
        "products",
        "inventory",
    }
    assert unload_data["records_cleared"] == 5170  # 1250 + 3420 + 250 + 250
    assert "unloaded successfully" in unload_data["message"]

    # 3. Verify datasets are completely removed from SQLite
    cleared_res = test_client.get("/api/v1/datasets?scenario_id=monday_revenue_mystery")
    assert cleared_res.status_code == 200
    assert cleared_res.json() == []

    # 4. Verify EVERY .csv file on disk is completely unaltered
    for file_name, (expected_size, expected_bytes) in csv_snapshots.items():
        file_path = fixtures_dir / file_name
        assert file_path.exists(), f"CSV fixture file '{file_name}' must not be deleted!"
        assert file_path.stat().st_size == expected_size, f"CSV fixture '{file_name}' size altered!"
        assert file_path.read_bytes() == expected_bytes, (
            f"CSV fixture '{file_name}' content altered!"
        )

    # 5. Verify idempotent re-unload
    idempotent_res = test_client.post("/api/v1/scenarios/monday_revenue_mystery/unload")
    assert idempotent_res.status_code == 200
    assert idempotent_res.json()["unloaded_datasets"] == []
    assert idempotent_res.json()["records_cleared"] == 0
