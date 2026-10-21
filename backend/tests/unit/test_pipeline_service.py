"""Unit tests for PipelineHistoryService, status evaluation, and seeding."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.scenario import Scenario
from app.schemas.pipeline import (
    PipelineExecutionStatus,
    PipelineRunResponse,
    QualityHealthStatus,
)
from app.schemas.validation import RuleSeverity, RuleStatus
from app.services.pipeline.service import (
    PipelineHistoryService,
    parse_iso_datetime,
)


def test_parse_iso_datetime() -> None:
    """Verify ISO datetime string parsing handles various formats safely."""
    assert parse_iso_datetime(None) is None
    assert parse_iso_datetime("") is None
    assert parse_iso_datetime("not-a-datetime") is None

    dt1 = parse_iso_datetime("2026-10-20T02:00:00Z")
    assert dt1 is not None
    assert dt1.year == 2026
    assert dt1.month == 10
    assert dt1.day == 20
    assert dt1.hour == 2

    dt2 = parse_iso_datetime("2026-10-20T02:00:00+00:00")
    assert dt2 is not None
    assert dt2 == dt1


def test_evaluate_quality_health_unvalidated() -> None:
    """Verify unvalidated state when no checks have been evaluated."""
    status = PipelineHistoryService.evaluate_quality_health(
        findings=None,
        total_checks_evaluated=0,
    )
    assert status == QualityHealthStatus.UNVALIDATED

    status_empty = PipelineHistoryService.evaluate_quality_health(
        findings=[],
        total_checks_evaluated=0,
    )
    assert status_empty == QualityHealthStatus.UNVALIDATED


def test_evaluate_quality_health_healthy() -> None:
    """Verify healthy status when checks were evaluated and no issues found."""
    status = PipelineHistoryService.evaluate_quality_health(
        findings=[],
        total_checks_evaluated=10,
    )
    assert status == QualityHealthStatus.HEALTHY

    # Findings that are all PASSED
    findings = [
        {"status": RuleStatus.PASSED, "severity": RuleSeverity.CRITICAL},
        {"status": "PASSED", "severity": "HIGH"},
    ]
    status = PipelineHistoryService.evaluate_quality_health(
        findings=findings,
        total_checks_evaluated=2,
    )
    assert status == QualityHealthStatus.HEALTHY


def test_evaluate_quality_health_warning() -> None:
    """Verify warning status for low/medium severity or warning status findings."""
    findings_warning = [
        {"status": RuleStatus.WARNING, "severity": RuleSeverity.MEDIUM},
    ]
    status = PipelineHistoryService.evaluate_quality_health(
        findings=findings_warning,
        total_checks_evaluated=5,
    )
    assert status == QualityHealthStatus.WARNING

    findings_low_failed = [
        {"status": RuleStatus.FAILED, "severity": RuleSeverity.LOW},
    ]
    status = PipelineHistoryService.evaluate_quality_health(
        findings=findings_low_failed,
        total_checks_evaluated=5,
    )
    assert status == QualityHealthStatus.WARNING


def test_evaluate_quality_health_degraded() -> None:
    """Verify degraded status when high severity failures are present."""
    findings = [
        {"status": RuleStatus.FAILED, "severity": RuleSeverity.HIGH},
        {"status": RuleStatus.WARNING, "severity": RuleSeverity.LOW},
    ]
    status = PipelineHistoryService.evaluate_quality_health(
        findings=findings,
        total_checks_evaluated=5,
    )
    assert status == QualityHealthStatus.DEGRADED


def test_evaluate_quality_health_corrupted() -> None:
    """Verify corrupted status when critical severity failures are present."""
    findings = [
        {"status": RuleStatus.FAILED, "severity": RuleSeverity.CRITICAL},
        {"status": RuleStatus.FAILED, "severity": RuleSeverity.HIGH},
    ]
    status = PipelineHistoryService.evaluate_quality_health(
        findings=findings,
        total_checks_evaluated=5,
    )
    assert status == QualityHealthStatus.CORRUPTED


def test_seed_and_get_pipeline_runs(db_session: Session) -> None:
    """Verify pipeline runs can be seeded, queried, and retrieved by ID."""
    now = datetime.now(UTC)
    scenario = Scenario(
        id="test_pipeline_scenario",
        name="Test Pipeline Scenario",
        active_fixture_version="defective",
        created_at=now,
        updated_at=now,
    )
    db_session.add(scenario)
    db_session.commit()

    runs_data: list[dict[str, Any]] = [
        {
            "id": "run_001",
            "pipeline_name": "daily_etl",
            "execution_status": PipelineExecutionStatus.COMPLETED_SUCCESS.value,
            "quality_health": QualityHealthStatus.HEALTHY.value,
            "start_time": "2026-10-18T02:00:00Z",
            "end_time": "2026-10-18T02:05:00Z",
            "duration_ms": 300000,
            "records_ingested": 1000,
            "records_written": 1000,
            "error_message": None,
            "run_log": [
                {"step": "extract", "status": "SUCCESS", "records": 1000, "duration_ms": 100000},
                {"step": "load", "status": "SUCCESS", "records": 1000, "duration_ms": 200000},
            ],
        },
        {
            "id": "run_002",
            "pipeline_name": "daily_etl",
            "execution_status": PipelineExecutionStatus.COMPLETED_SUCCESS.value,
            "quality_health": QualityHealthStatus.CORRUPTED.value,
            "start_time": "2026-10-19T02:00:00Z",
            "end_time": "2026-10-19T02:06:00Z",
            "duration_ms": 360000,
            "records_ingested": 1200,
            "records_written": 1150,
            "error_message": None,
            "run_log": [
                {"step": "extract", "status": "SUCCESS", "records": 1200, "duration_ms": 120000},
                {"step": "load", "status": "SUCCESS", "records": 1150, "duration_ms": 240000},
            ],
        },
    ]

    seeded = PipelineHistoryService.seed_pipeline_runs(
        db=db_session,
        scenario_id="test_pipeline_scenario",
        runs_data=runs_data,
    )
    assert len(seeded) == 2

    # Query all runs for scenario (sorted desc by start_time: run_002 first, then run_001)
    runs = PipelineHistoryService.get_runs(db=db_session, scenario_id="test_pipeline_scenario")
    assert len(runs) == 2
    assert runs[0].id == "run_002"
    assert runs[1].id == "run_001"

    # Query by ID
    run2 = PipelineHistoryService.get_run_by_id(db=db_session, run_id="run_002")
    assert run2.id == "run_002"
    assert run2.execution_status == PipelineExecutionStatus.COMPLETED_SUCCESS.value
    assert run2.quality_health == QualityHealthStatus.CORRUPTED.value

    # NotFoundError for unknown run ID
    with pytest.raises(NotFoundError):
        PipelineHistoryService.get_run_by_id(db=db_session, run_id="run_unknown")


def test_pipeline_run_response_schema_step_logs() -> None:
    """Verify PipelineRunResponse properly parses structured and fallback step logs."""
    from app.models.pipeline import PipelineRun

    now = datetime.now(UTC)
    model = PipelineRun(
        id="test_schema_run",
        scenario_id="test_scen",
        pipeline_name="pipe",
        execution_status="COMPLETED_SUCCESS",
        quality_health="CORRUPTED",
        start_time=now,
        end_time=now,
        duration_ms=5000,
        records_ingested=10,
        records_written=10,
        error_message=None,
        run_log=json.dumps(
            [
                {"step": "step1", "status": "SUCCESS", "records": 10, "duration_ms": 2000},
                "Simple string log item",
            ]
        ),
        created_at=now,
    )

    resp = PipelineRunResponse.from_model(model, include_logs=True)
    assert resp.id == "test_schema_run"
    assert len(resp.run_log) == 2
    assert resp.run_log[0].step == "step1"
    assert resp.run_log[0].records == 10
    assert resp.run_log[1].step == "Simple string log item"

    # Without logs
    resp_no_logs = PipelineRunResponse.from_model(model, include_logs=False)
    assert len(resp_no_logs.run_log) == 0

    # Malformed logs
    model.run_log = "invalid json {"
    resp_malformed = PipelineRunResponse.from_model(model, include_logs=True)
    assert resp_malformed.run_log == []
