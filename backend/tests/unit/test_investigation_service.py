"""Unit tests for Investigation workspace service and schema integration."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.dataset import Dataset
from app.models.scenario import Scenario
from app.models.validation import ValidationFinding, ValidationRule, ValidationRun
from app.schemas.investigation import (
    InvestigationCreateRequest,
    InvestigationItem,
    InvestigationItemType,
    InvestigationResponse,
    InvestigationStatus,
    InvestigationUpdateRequest,
    _safe_parse_str_list,
)
from app.services.reports.investigation import InvestigationService


@pytest.fixture
def test_scenario(db_session: Session) -> Scenario:
    """Seed a test scenario into SQLite."""
    scenario = Scenario(
        id="test_scen_inv",
        name="Test Investigation Scenario",
        description="Scenario for unit testing investigations",
        category="testing",
        is_bundled=True,
        active_fixture_version="defective",
        created_at=datetime.now(UTC),
    )
    db_session.add(scenario)
    db_session.commit()
    return scenario


@pytest.fixture
def test_finding(db_session: Session, test_scenario: Scenario) -> ValidationFinding:
    """Seed a test validation finding."""
    dataset = Dataset(
        id="orders_test_inv",
        scenario_id=test_scenario.id,
        name="orders.csv",
        file_path="data/test/orders.csv",
        file_format="csv",
        file_size_bytes=1024,
        record_count=1250,
        column_count=5,
        schema_definition="[]",
        created_at=datetime.now(UTC),
    )
    val_run = ValidationRun(
        id="val_run_inv_test",
        scenario_id=test_scenario.id,
        fixture_version="defective",
        status="FAILED",
        total_checks=1,
        passed_checks=0,
        failed_checks=1,
        warning_checks=0,
        skipped_checks=0,
        error_checks=0,
        execution_duration_ms=12,
        executed_at=datetime.now(UTC),
    )
    rule = ValidationRule(
        id="RULE_TEST_INV_1",
        scenario_id=test_scenario.id,
        dataset_id=dataset.id,
        name="Test Rule Inv",
        category="UNIQUENESS",
        severity="CRITICAL",
        parameters="{}",
        is_active=True,
    )
    finding = ValidationFinding(
        id="val_find_inv_1",
        run_id=val_run.id,
        rule_id=rule.id,
        dataset_id=dataset.id,
        rule_category="UNIQUENESS",
        severity="CRITICAL",
        status="FAILED",
        affected_fields='["order_id"]',
        affected_record_count=15,
        total_record_count=1250,
        message="15 duplicate order IDs found",
        evidence='{"duplicates": [1001, 1002]}',
        execution_duration_ms=5,
        created_at=datetime.now(UTC),
    )
    db_session.add(dataset)
    db_session.add(val_run)
    db_session.add(rule)
    db_session.add(finding)
    db_session.commit()
    return finding


def test_schema_fact_hypothesis_separation() -> None:
    """Assert facts and hypotheses are distinctly typed and cannot be confused in schema."""
    item_fact = InvestigationItem(
        item_type=InvestigationItemType.VERIFIED_FACT,
        content="15 duplicate rows detected in orders.csv",
        source="VAL-ORD-001",
    )
    item_hypo = InvestigationItem(
        item_type=InvestigationItemType.HYPOTHESIS,
        content="Upstream retry mechanism duplicated messages",
        source="engineer",
    )
    item_action = InvestigationItem(
        item_type=InvestigationItemType.ACTION_ITEM,
        content="Deduplicate using idempotent pipeline step",
    )

    assert item_fact.item_type != item_hypo.item_type
    assert item_fact.item_type == InvestigationItemType.VERIFIED_FACT
    assert item_hypo.item_type == InvestigationItemType.HYPOTHESIS
    assert item_action.item_type == InvestigationItemType.ACTION_ITEM

    # Create request validates distinct non-overlapping list fields
    req = InvestigationCreateRequest(
        scenario_id="scen_1",
        title="Test Investigation",
        verified_facts=["Observed 15 dups"],
        hypotheses=["Possible network retry"],
        action_items=["Add idempotency key"],
    )
    assert req.verified_facts == ["Observed 15 dups"]
    assert req.hypotheses == ["Possible network retry"]
    assert req.action_items == ["Add idempotency key"]


def test_safe_parse_str_list_edge_cases() -> None:
    """Verify robust JSON string parsing and fallback handling."""
    assert _safe_parse_str_list(None) == []
    assert _safe_parse_str_list("") == []
    assert _safe_parse_str_list([]) == []
    assert _safe_parse_str_list('["fact1", "fact2"]') == ["fact1", "fact2"]
    assert _safe_parse_str_list("single unquoted fact") == ["single unquoted fact"]
    assert _safe_parse_str_list(123) == []  # type: ignore[arg-type]


def test_create_investigation_success(db_session: Session, test_scenario: Scenario) -> None:
    """Verify creating an investigation with facts, hypotheses, and action items."""
    req = InvestigationCreateRequest(
        scenario_id=test_scenario.id,
        title="Duplicate Order Investigation",
        status=InvestigationStatus.OPEN,
        verified_facts=["15 duplicate order IDs found in orders.csv"],
        hypotheses=["Retry storm on checkout webhooks"],
        action_items=["Deploy deduplication transform"],
    )

    inv = InvestigationService.create_investigation(db=db_session, request=req)
    assert inv.id.startswith("inv_")
    assert inv.scenario_id == test_scenario.id
    assert inv.title == "Duplicate Order Investigation"
    assert inv.status == "OPEN"
    assert json.loads(inv.verified_facts) == ["15 duplicate order IDs found in orders.csv"]
    assert json.loads(inv.hypotheses) == ["Retry storm on checkout webhooks"]
    assert json.loads(inv.action_items) == ["Deploy deduplication transform"]

    # Verify response schema conversion
    resp = InvestigationResponse.from_model(inv)
    assert resp.id == inv.id
    assert resp.verified_facts == ["15 duplicate order IDs found in orders.csv"]
    assert resp.hypotheses == ["Retry storm on checkout webhooks"]
    assert resp.action_items == ["Deploy deduplication transform"]


def test_create_investigation_empty_action_items(
    db_session: Session, test_scenario: Scenario
) -> None:
    """Edge Case: Empty action items list is preserved as empty list and handled cleanly."""
    req = InvestigationCreateRequest(
        scenario_id=test_scenario.id,
        title="Investigation Without Initial Actions",
        verified_facts=["Pipeline completed with exit 0"],
        hypotheses=["Transient database lag"],
        action_items=[],
    )

    inv = InvestigationService.create_investigation(db=db_session, request=req)
    assert inv.action_items == "[]"

    resp = InvestigationResponse.from_model(inv)
    assert resp.action_items == []


def test_create_investigation_with_initial_finding(
    db_session: Session, test_scenario: Scenario, test_finding: ValidationFinding
) -> None:
    """Verify linking an investigation to a validated initial finding."""
    req = InvestigationCreateRequest(
        scenario_id=test_scenario.id,
        title="Anchored Investigation",
        initial_finding_id=test_finding.id,
        verified_facts=["Triggered by rule " + test_finding.rule_id],
        hypotheses=[],
        action_items=[],
    )

    inv = InvestigationService.create_investigation(db=db_session, request=req)
    assert inv.initial_finding_id == test_finding.id


def test_create_investigation_invalid_scenario(db_session: Session) -> None:
    """Attempting to create an investigation for a non-existent scenario raises NotFoundError."""
    req = InvestigationCreateRequest(
        scenario_id="non_existent_scen",
        title="Invalid Scenario",
    )
    with pytest.raises(NotFoundError) as exc_info:
        InvestigationService.create_investigation(db=db_session, request=req)
    assert exc_info.value.code == "SCENARIO_NOT_FOUND"


def test_create_investigation_invalid_finding(db_session: Session, test_scenario: Scenario) -> None:
    """Attempting to link a non-existent initial finding raises NotFoundError."""
    req = InvestigationCreateRequest(
        scenario_id=test_scenario.id,
        title="Invalid Finding",
        initial_finding_id="fake_finding_id",
    )
    with pytest.raises(NotFoundError) as exc_info:
        InvestigationService.create_investigation(db=db_session, request=req)
    assert exc_info.value.code == "FINDING_NOT_FOUND"


def test_get_and_list_investigations(db_session: Session, test_scenario: Scenario) -> None:
    """Verify retrieving and filtering investigations."""
    inv1 = InvestigationService.create_investigation(
        db=db_session,
        request=InvestigationCreateRequest(
            scenario_id=test_scenario.id,
            title="Inv 1",
            status=InvestigationStatus.OPEN,
        ),
    )
    inv2 = InvestigationService.create_investigation(
        db=db_session,
        request=InvestigationCreateRequest(
            scenario_id=test_scenario.id,
            title="Inv 2",
            status=InvestigationStatus.INVESTIGATING,
        ),
    )

    fetched = InvestigationService.get_investigation(db=db_session, investigation_id=inv1.id)
    assert fetched.id == inv1.id

    # List all
    items, total = InvestigationService.list_investigations(
        db=db_session, scenario_id=test_scenario.id
    )
    assert total >= 2
    ids = [i.id for i in items]
    assert inv1.id in ids
    assert inv2.id in ids

    # Filter by status
    investigating_items, total_inv = InvestigationService.list_investigations(
        db=db_session, scenario_id=test_scenario.id, status="INVESTIGATING"
    )
    assert total_inv == 1
    assert investigating_items[0].id == inv2.id


def test_update_investigation(db_session: Session, test_scenario: Scenario) -> None:
    """Verify partial updates to title, status, facts, hypotheses, and action items."""
    inv = InvestigationService.create_investigation(
        db=db_session,
        request=InvestigationCreateRequest(
            scenario_id=test_scenario.id,
            title="Initial Title",
            status=InvestigationStatus.OPEN,
            verified_facts=["Fact 1"],
            hypotheses=["Hypo 1"],
            action_items=[],
        ),
    )

    update_req = InvestigationUpdateRequest(
        title="Updated Title",
        status=InvestigationStatus.RESOLVED,
        hypotheses=["Hypo 1", "Hypo 2 (Confirmed)"],
        action_items=["Backfill completed"],
    )

    updated = InvestigationService.update_investigation(
        db=db_session, investigation_id=inv.id, request=update_req
    )
    assert updated.title == "Updated Title"
    assert updated.status == "RESOLVED"
    assert json.loads(updated.verified_facts) == ["Fact 1"]  # Unchanged
    assert json.loads(updated.hypotheses) == ["Hypo 1", "Hypo 2 (Confirmed)"]
    assert json.loads(updated.action_items) == ["Backfill completed"]


def test_delete_investigation(db_session: Session, test_scenario: Scenario) -> None:
    """Verify deleting an investigation workspace."""
    inv = InvestigationService.create_investigation(
        db=db_session,
        request=InvestigationCreateRequest(
            scenario_id=test_scenario.id,
            title="To Delete",
        ),
    )

    InvestigationService.delete_investigation(db=db_session, investigation_id=inv.id)

    with pytest.raises(NotFoundError):
        InvestigationService.get_investigation(db=db_session, investigation_id=inv.id)
