"""Unit tests for RecoveryService, fixture swapping, and diff calculations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.core.errors import LuxException, NotFoundError
from app.models.scenario import Scenario
from app.models.validation import ValidationFinding, ValidationRun
from app.services.ingestion.loader import ScenarioLoaderService
from app.services.validation.recovery import RecoveryService
from app.services.validation.runner import ValidationRunnerService


def test_swap_fixtures_invalid_version(db_session: Session) -> None:
    """Verify swap_fixtures raises LuxException for invalid fixture version."""
    with pytest.raises(LuxException) as exc_info:
        RecoveryService.swap_fixtures("monday_revenue_mystery", "unknown_ver", db_session)
    assert exc_info.value.code == "INVALID_FIXTURE_VERSION"


def test_swap_fixtures_scenario_not_found(db_session: Session) -> None:
    """Verify swap_fixtures raises NotFoundError when scenario is not in DB."""
    with pytest.raises(NotFoundError) as exc_info:
        RecoveryService.swap_fixtures("non_existent_scenario", "corrected", db_session)
    assert exc_info.value.code == "SCENARIO_NOT_FOUND"


def test_verify_recovery_scenario_not_found(db_session: Session) -> None:
    """Verify verify_recovery raises NotFoundError when scenario is not in DB."""
    with pytest.raises(NotFoundError) as exc_info:
        RecoveryService.verify_recovery("non_existent_scenario", db_session)
    assert exc_info.value.code == "SCENARIO_NOT_FOUND"


def test_swap_fixtures_and_verify_recovery_live(db_session: Session) -> None:
    """Verify live execution of swap_fixtures and verify_recovery through service directly."""
    # 1. Load defective scenario
    ScenarioLoaderService.load_scenario("monday_revenue_mystery", "defective", db_session)

    # 2. Swap to corrected
    RecoveryService.swap_fixtures("monday_revenue_mystery", "corrected", db_session)

    scenario = db_session.query(Scenario).filter_by(id="monday_revenue_mystery").one()
    assert scenario.active_fixture_version == "corrected"

    # 3. Swap back to defective
    RecoveryService.swap_fixtures("monday_revenue_mystery", "defective", db_session)
    assert scenario.active_fixture_version == "defective"

    # 4. Verify recovery service directly
    res = RecoveryService.verify_recovery("monday_revenue_mystery", db_session)

    assert res.scenario_id == "monday_revenue_mystery"
    assert res.comparison.previous_run.failed_checks == 4
    assert res.comparison.previous_run.quality_health == "CORRUPTED"
    assert res.comparison.current_run.failed_checks == 0
    assert res.comparison.current_run.quality_health == "HEALTHY"
    assert len(res.comparison.resolved_findings) == 4
    assert all(item.status == "RESOLVED" for item in res.comparison.resolved_findings)
    assert res.comparison.downstream_recovery_status == "ALL_ASSETS_HEALTHY"


def test_verify_recovery_partial_recovery_handling(db_session: Session) -> None:
    """Verify that if one check remains failed, the diff reports PARTIALLY_RECOVERED."""
    # 1. Load defective scenario and run baseline
    ScenarioLoaderService.load_scenario("monday_revenue_mystery", "defective", db_session)
    ValidationRunnerService.execute_validation_run("monday_revenue_mystery", db_session)

    # 2. Define a fake execution for the recovery run that still has VAL-INV-001 failing
    def fake_execute_recovery_run(
        scenario_id: str, db: Session, dataset_ids: list[str] | None = None
    ) -> ValidationRun:
        run_id = f"val_run_partial_{uuid.uuid4().hex[:6]}"
        now = datetime.now(UTC)
        run = ValidationRun(
            id=run_id,
            scenario_id=scenario_id,
            fixture_version="corrected",
            status="FAILED",
            total_checks=8,
            passed_checks=7,
            failed_checks=1,
            warning_checks=0,
            skipped_checks=0,
            error_checks=0,
            execution_duration_ms=45,
            executed_at=now,
        )
        db.add(run)

        # 3 resolved checks (PASSED)
        for r_id, ds_id in [
            ("VAL-ORD-001", "orders"),
            ("VAL-ORD-002", "order_items"),
            ("VAL-FRESH-001", "orders"),
        ]:
            db.add(
                ValidationFinding(
                    id=f"f_{uuid.uuid4().hex[:6]}",
                    run_id=run_id,
                    rule_id=r_id,
                    dataset_id=ds_id,
                    rule_category="CATEGORY",
                    severity="HIGH",
                    status="PASSED",
                    affected_fields="[]",
                    affected_record_count=0,
                    total_record_count=100,
                    message="Clean check passed",
                    evidence="{}",
                    execution_duration_ms=5,
                    created_at=now,
                )
            )

        # 1 unresolved check (FAILED)
        db.add(
            ValidationFinding(
                id=f"f_{uuid.uuid4().hex[:6]}",
                run_id=run_id,
                rule_id="VAL-INV-001",
                dataset_id="inventory",
                rule_category="VALUE_RANGE",
                severity="HIGH",
                status="FAILED",
                affected_fields='["quantity_on_hand"]',
                affected_record_count=2,
                total_record_count=100,
                message="Negative inventory found",
                evidence="{}",
                execution_duration_ms=5,
                created_at=now,
            )
        )
        db.commit()
        db.refresh(run)
        return run

    with patch(
        "app.services.validation.recovery.ValidationRunnerService.execute_validation_run",
        side_effect=fake_execute_recovery_run,
    ):
        res = RecoveryService.verify_recovery("monday_revenue_mystery", db_session)

    assert res.scenario_id == "monday_revenue_mystery"
    assert res.comparison.previous_run.failed_checks == 4
    assert res.comparison.current_run.failed_checks == 1
    assert res.comparison.current_run.quality_health in ("DEGRADED", "CORRUPTED")
    assert res.comparison.downstream_recovery_status == "PARTIALLY_RECOVERED"

    findings_map = {f.rule_id: f for f in res.comparison.resolved_findings}
    assert findings_map["VAL-ORD-001"].status == "RESOLVED"
    assert findings_map["VAL-ORD-002"].status == "RESOLVED"
    assert findings_map["VAL-FRESH-001"].status == "RESOLVED"
    assert findings_map["VAL-INV-001"].status == "UNRESOLVED"
