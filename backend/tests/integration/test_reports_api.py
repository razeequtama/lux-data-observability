"""Integration tests for safe incident report generation and artifact export API."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import LuxException
from app.db.session import get_db
from app.main import app
from app.models.investigation import ReportArtifact
from app.schemas.report import IncidentReportData
from app.services.reports.generator import ReportGeneratorService


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
def scenario_with_validations(test_client: TestClient) -> dict[str, str]:
    """Load scenario and execute validations, returning scenario and run identifiers."""
    # 1. Load defective scenario
    resp = test_client.post(
        "/api/v1/scenarios/monday_revenue_mystery/load",
        json={"fixture_version": "defective"},
    )
    assert resp.status_code == 200, resp.text

    # 2. Execute validation run
    val_resp = test_client.post(
        "/api/v1/validations/run",
        json={"scenario_id": "monday_revenue_mystery"},
    )
    assert val_resp.status_code == 200, val_resp.text
    run_id = val_resp.json()["run_id"]

    return {
        "scenario_id": "monday_revenue_mystery",
        "validation_run_id": run_id,
    }


def test_generate_report_api_success(
    test_client: TestClient, scenario_with_validations: dict[str, str]
) -> None:
    """POST /api/v1/reports/generate generates JSON and HTML artifacts and returns 201 Created."""
    payload = {
        "scenario_id": scenario_with_validations["scenario_id"],
        "validation_run_id": scenario_with_validations["validation_run_id"],
        "title": "Investigation: Monday Morning Revenue Anomaly",
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

    resp = test_client.post("/api/v1/reports/generate", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["report_id"].startswith("rep_")
    assert data["investigation_id"].startswith("inv_")
    assert "generated_at" in data
    assert f"/api/v1/reports/{data['report_id']}/export?format=json" == data["json_url"]
    assert f"/api/v1/reports/{data['report_id']}/export?format=html" == data["html_url"]

    # Verify physical file existence in settings.artifacts_dir
    json_path = settings.artifacts_dir / f"{data['report_id']}.json"
    html_path = settings.artifacts_dir / f"{data['report_id']}.html"
    assert json_path.exists(), f"File {json_path} was not created"
    assert html_path.exists(), f"File {html_path} was not created"


def test_export_report_json(
    test_client: TestClient, scenario_with_validations: dict[str, str]
) -> None:
    """GET /api/v1/reports/{id}/export?format=json returns valid, structured incident report."""
    gen_resp = test_client.post(
        "/api/v1/reports/generate",
        json={"scenario_id": scenario_with_validations["scenario_id"]},
    )
    assert gen_resp.status_code == 201
    report_id = gen_resp.json()["report_id"]

    export_resp = test_client.get(f"/api/v1/reports/{report_id}/export?format=json")
    assert export_resp.status_code == 200
    assert "application/json" in export_resp.headers["content-type"]

    data = export_resp.json()
    assert data["report_id"] == report_id
    assert data["scenario"]["id"] == "monday_revenue_mystery"
    assert "validation_summary" in data
    assert data["validation_summary"]["quality_health"] == "CORRUPTED"
    assert len(data["findings"]) >= 4

    # Assert findings contain sample keys & evidence
    dup_finding = next((f for f in data["findings"] if f["rule_id"] == "VAL-ORD-001"), None)
    assert dup_finding is not None
    assert dup_finding["status"] == "FAILED"
    assert len(dup_finding["sample_keys"]) > 0

    # Assert integrity hash present
    assert "sha256" in data["integrity"]
    assert len(data["integrity"]["sha256"]) == 64


def test_export_report_html(
    test_client: TestClient, scenario_with_validations: dict[str, str]
) -> None:
    """GET /api/v1/reports/{id}/export?format=html returns safe standalone HTML with CSP."""
    gen_resp = test_client.post(
        "/api/v1/reports/generate",
        json={"scenario_id": scenario_with_validations["scenario_id"]},
    )
    assert gen_resp.status_code == 201
    report_id = gen_resp.json()["report_id"]

    export_resp = test_client.get(f"/api/v1/reports/{report_id}/export?format=html")
    assert export_resp.status_code == 200
    assert "text/html" in export_resp.headers["content-type"]

    # Verify HTTP Header CSP
    csp_header = export_resp.headers.get("Content-Security-Policy", "")
    assert "default-src 'none'" in csp_header
    assert "style-src 'unsafe-inline'" in csp_header
    assert "sandbox" in csp_header

    # Verify In-body HTML CSP Meta Tag
    html_text = export_resp.text
    assert '<meta http-equiv="Content-Security-Policy"' in html_text
    assert "default-src 'none'" in html_text

    # Verify Lux Purple branding token
    assert "#6B46C1" in html_text or "var(--primary)" in html_text

    # Verify collapsible evidence panels
    assert "<details" in html_text
    assert "<summary>" in html_text

    # Verify zero external scripts or links
    assert "<script" not in html_text
    assert '<link rel="stylesheet"' not in html_text


def test_generate_report_auto_synthesis(
    test_client: TestClient, scenario_with_validations: dict[str, str]
) -> None:
    """When facts/hypotheses are omitted, service synthesizes evidence automatically."""
    resp = test_client.post(
        "/api/v1/reports/generate",
        json={"scenario_id": scenario_with_validations["scenario_id"]},
    )
    assert resp.status_code == 201
    report_id = resp.json()["report_id"]

    export_resp = test_client.get(f"/api/v1/reports/{report_id}/export?format=json")
    assert export_resp.status_code == 200
    report_json = export_resp.json()

    # Verified facts should have been synthesized from pipeline and findings
    assert len(report_json["investigation"]["verified_facts"]) > 0
    assert any(
        "Rule VAL-ORD-001" in fact or "duplicate" in fact.lower()
        for fact in report_json["investigation"]["verified_facts"]
    )


def test_get_report_artifacts_by_id(
    test_client: TestClient, scenario_with_validations: dict[str, str]
) -> None:
    """GET /api/v1/reports/{report_id} returns both JSON and HTML artifact metadata."""
    gen_resp = test_client.post(
        "/api/v1/reports/generate",
        json={"scenario_id": scenario_with_validations["scenario_id"]},
    )
    assert gen_resp.status_code == 201
    report_id = gen_resp.json()["report_id"]

    artifacts_resp = test_client.get(f"/api/v1/reports/{report_id}")
    assert artifacts_resp.status_code == 200
    artifacts = artifacts_resp.json()

    assert len(artifacts) == 2
    formats = {a["format"] for a in artifacts}
    assert formats == {"json", "html"}
    assert all(a["file_size_bytes"] > 0 for a in artifacts)
    assert all(len(a["sha256_hash"]) == 64 for a in artifacts)


def test_list_report_artifacts(
    test_client: TestClient, scenario_with_validations: dict[str, str]
) -> None:
    """GET /api/v1/reports lists persisted report artifacts."""
    # Generate at least one report
    test_client.post(
        "/api/v1/reports/generate",
        json={"scenario_id": scenario_with_validations["scenario_id"]},
    )

    resp = test_client.get(
        f"/api/v1/reports?scenario_id={scenario_with_validations['scenario_id']}"
    )
    assert resp.status_code == 200
    artifacts = resp.json()
    assert len(artifacts) >= 2


def test_export_invalid_format_error(
    test_client: TestClient, scenario_with_validations: dict[str, str]
) -> None:
    """GET /api/v1/reports/{id}/export?format=invalid returns 400 Bad Request."""
    gen_resp = test_client.post(
        "/api/v1/reports/generate",
        json={"scenario_id": scenario_with_validations["scenario_id"]},
    )
    report_id = gen_resp.json()["report_id"]

    resp = test_client.get(f"/api/v1/reports/{report_id}/export?format=exe")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_REPORT_FORMAT"


def test_export_nonexistent_report_404(test_client: TestClient) -> None:
    """GET /api/v1/reports/rep_unknown/export returns 404 Not Found."""
    resp = test_client.get("/api/v1/reports/rep_nonexistent999/export?format=json")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "REPORT_NOT_FOUND"


def test_generate_report_invalid_scenario_404(test_client: TestClient) -> None:
    """POST /api/v1/reports/generate with unknown scenario returns 404 Not Found."""
    resp = test_client.post(
        "/api/v1/reports/generate",
        json={"scenario_id": "nonexistent_scenario"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "SCENARIO_NOT_FOUND"


def test_generate_report_with_existing_investigation(
    test_client: TestClient, scenario_with_validations: dict[str, str]
) -> None:
    """POST /api/v1/reports/generate linking to existing investigation workspace."""
    # 1. Create investigation workspace
    inv_resp = test_client.post(
        "/api/v1/investigations",
        json={
            "scenario_id": scenario_with_validations["scenario_id"],
            "title": "Pre-existing Investigation Workspace",
            "verified_facts": ["Existing Fact 1"],
            "hypotheses": ["Existing Hypothesis 1"],
            "action_items": ["Existing Action 1"],
        },
    )
    assert inv_resp.status_code == 201
    inv_id = inv_resp.json()["id"]

    # 2. Generate report referencing inv_id
    rep_resp = test_client.post(
        "/api/v1/reports/generate",
        json={
            "scenario_id": scenario_with_validations["scenario_id"],
            "investigation_id": inv_id,
        },
    )
    assert rep_resp.status_code == 201
    assert rep_resp.json()["investigation_id"] == inv_id


def test_exported_json_satisfies_pydantic_schema(
    test_client: TestClient, scenario_with_validations: dict[str, str]
) -> None:
    """Acceptance Criterion: Exported JSON report strictly satisfies the report JSON schema."""
    gen_resp = test_client.post(
        "/api/v1/reports/generate",
        json={"scenario_id": scenario_with_validations["scenario_id"]},
    )
    assert gen_resp.status_code == 201
    report_id = gen_resp.json()["report_id"]

    export_resp = test_client.get(f"/api/v1/reports/{report_id}/export?format=json")
    assert export_resp.status_code == 200

    # Parse and validate with Pydantic model
    parsed_report = IncidentReportData.model_validate(export_resp.json())
    assert parsed_report.report_id == report_id
    assert parsed_report.scenario["id"] == scenario_with_validations["scenario_id"]
    assert len(parsed_report.findings) > 0


def test_path_traversal_protection(
    db_session: Session, scenario_with_validations: dict[str, str]
) -> None:
    """Security Defense: Path traversal attempt outside artifacts directory is blocked."""
    from app.schemas.investigation import InvestigationCreateRequest
    from app.services.reports.investigation import InvestigationService

    inv = InvestigationService.create_investigation(
        db=db_session,
        request=InvestigationCreateRequest(
            scenario_id=scenario_with_validations["scenario_id"],
            title="Path Traversal Test Workspace",
        ),
    )

    # Attempt to point an artifact to an unauthorized system path
    malicious_artifact = ReportArtifact(
        id="rep_malicious_json",
        investigation_id=inv.id,
        scenario_id=scenario_with_validations["scenario_id"],
        validation_run_id=scenario_with_validations["validation_run_id"],
        format="json",
        file_path=str(Path("/etc/passwd").resolve()),
        sha256_hash="0" * 64,
        file_size_bytes=100,
    )
    db_session.add(malicious_artifact)
    db_session.commit()

    with pytest.raises(LuxException) as exc_info:
        ReportGeneratorService.get_report_artifact(
            db=db_session, report_id="rep_malicious", export_format="json"
        )
    assert exc_info.value.code == "PATH_TRAVERSAL_DETECTED"
