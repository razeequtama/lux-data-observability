"""Validation runner service executing declarative rules and persisting structured findings."""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.errors import LuxException, NotFoundError
from app.models.dataset import Dataset
from app.models.scenario import Scenario
from app.models.validation import ValidationFinding, ValidationRule, ValidationRun
from app.schemas.validation import RuleCategory, RuleSeverity, RuleStatus
from app.services.validation.base import ValidationContext
from app.services.validation.registry import RuleRegistry

logger = logging.getLogger("lux.validation.runner")


def _cap_evidence_samples(evidence: dict[str, Any], max_samples: int = 50) -> dict[str, Any]:
    """Recursively enforce that sample lists in diagnostic evidence do not exceed max_samples."""
    capped: dict[str, Any] = {}
    for key, val in evidence.items():
        if isinstance(val, list):
            if len(val) > max_samples:
                capped[key] = val[:max_samples]
                capped[f"{key}_truncated"] = True
                capped[f"{key}_total_count"] = len(val)
            else:
                capped[key] = val
        elif isinstance(val, dict):
            capped[key] = _cap_evidence_samples(val, max_samples=max_samples)
        else:
            capped[key] = val
    return capped


class ValidationRunnerService:
    """Service orchestrating execution of validation rules against scenario datasets."""

    @classmethod
    def execute_validation_run(
        cls,
        scenario_id: str,
        db: Session,
        dataset_ids: list[str] | None = None,
    ) -> ValidationRun:
        """Execute validation rules for target scenario and persist the run and findings."""
        # 1. Verify scenario exists
        scenario = db.execute(
            select(Scenario).where(Scenario.id == scenario_id)
        ).scalar_one_or_none()
        if not scenario:
            raise NotFoundError(
                code="SCENARIO_NOT_FOUND",
                message=(
                    f"Scenario '{scenario_id}' was not found in the database. "
                    "Please load the scenario first."
                ),
                details={"scenario_id": scenario_id},
            )

        # 2. Retrieve all scenario datasets
        all_datasets = (
            db.execute(select(Dataset).where(Dataset.scenario_id == scenario_id)).scalars().all()
        )
        if not all_datasets:
            logger.warning("Scenario '%s' has no registered datasets to validate.", scenario_id)

        dataset_map = {d.id: d for d in all_datasets}

        # 3. Resolve target datasets
        if dataset_ids is not None and len(dataset_ids) > 0:
            for d_id in dataset_ids:
                if d_id not in dataset_map:
                    raise NotFoundError(
                        code="DATASET_NOT_FOUND",
                        message=f"Dataset '{d_id}' was not found in scenario '{scenario_id}'.",
                        details={"dataset_id": d_id, "scenario_id": scenario_id},
                    )
            target_dataset_ids = set(dataset_ids)
        else:
            target_dataset_ids = set(dataset_map.keys())

        # 4. Build execution contexts for each dataset with cross-dataset accessibility
        contexts: dict[str, ValidationContext] = {}
        for d_id, ds in dataset_map.items():
            f_path = Path(ds.file_path)
            if not f_path.exists():
                raise LuxException(
                    code="DATASET_FILE_NOT_FOUND",
                    message=(
                        f"Dataset file '{ds.file_path}' for dataset '{d_id}' "
                        "does not exist on disk."
                    ),
                    details={"dataset_id": d_id, "file_path": ds.file_path},
                )
            contexts[d_id] = ValidationContext(
                dataset_id=d_id,
                file_path=f_path,
                file_format=ds.file_format,
                scenario_id=scenario_id,
                total_record_count=ds.record_count,
            )

        # Connect sibling contexts for cross-dataset queries (e.g. referential integrity)
        for sibling_ctx in contexts.values():
            sibling_ctx.datasets = contexts

        # 5. Query active validation rules for target datasets
        rules_query = (
            select(ValidationRule)
            .where(
                ValidationRule.scenario_id == scenario_id,
                ValidationRule.is_active.is_(True),
            )
            .order_by(ValidationRule.dataset_id, ValidationRule.id)
        )
        if target_dataset_ids:
            rules_query = rules_query.where(ValidationRule.dataset_id.in_(target_dataset_ids))

        rules = db.execute(rules_query).scalars().all()

        # 6. Execute rules and collect metrics
        run_id = f"val_run_{uuid.uuid4().hex[:8]}"
        now = datetime.now(UTC)

        total_checks = 0
        passed_checks = 0
        failed_checks = 0
        warning_checks = 0
        skipped_checks = 0
        error_checks = 0

        findings: list[ValidationFinding] = []
        start_run_time = time.perf_counter()

        for rule in rules:
            target_ctx = contexts.get(rule.dataset_id)
            if target_ctx is None:
                continue

            try:
                evaluator = RuleRegistry.create_rule(rule)
                eval_result = evaluator.evaluate(target_ctx)
            except Exception as exc:
                logger.exception("Unexpected error executing rule '%s': %s", rule.id, exc)
                eval_result = evaluator._build_result(
                    status=RuleStatus.ERROR,
                    affected_fields=[],
                    affected_record_count=0,
                    total_record_count=target_ctx.get_record_count(),
                    message=f"Rule evaluation failed unexpectedly: {exc}",
                    evidence={"error": str(exc), "error_type": exc.__class__.__name__},
                    duration_ms=0,
                )

            total_checks += 1
            status_str = (
                eval_result.status.value
                if isinstance(eval_result.status, RuleStatus)
                else str(eval_result.status).upper()
            )

            if status_str == RuleStatus.PASSED.value:
                passed_checks += 1
            elif status_str == RuleStatus.FAILED.value:
                failed_checks += 1
            elif status_str == RuleStatus.WARNING.value:
                warning_checks += 1
            elif status_str == RuleStatus.SKIPPED.value:
                skipped_checks += 1
            elif status_str == RuleStatus.ERROR.value:
                error_checks += 1

            # Cap diagnostic sample lists to prevent unbounded payloads
            capped_evidence = _cap_evidence_samples(eval_result.evidence, max_samples=50)

            finding_id = f"finding_{uuid.uuid4().hex[:8]}"
            finding = ValidationFinding(
                id=finding_id,
                run_id=run_id,
                rule_id=rule.id,
                dataset_id=rule.dataset_id,
                rule_category=(
                    eval_result.rule_category.value
                    if isinstance(eval_result.rule_category, RuleCategory)
                    else str(eval_result.rule_category)
                ),
                severity=(
                    eval_result.severity.value
                    if isinstance(eval_result.severity, RuleSeverity)
                    else str(eval_result.severity)
                ),
                status=status_str,
                affected_fields=json.dumps(eval_result.affected_fields),
                affected_record_count=eval_result.affected_record_count,
                total_record_count=eval_result.total_record_count,
                message=eval_result.message,
                evidence=json.dumps(capped_evidence),
                execution_duration_ms=eval_result.execution_duration_ms,
                created_at=now,
            )
            findings.append(finding)

        total_duration_ms = int((time.perf_counter() - start_run_time) * 1000)

        # 7. Determine overall run outcome status
        if failed_checks > 0 or error_checks > 0:
            overall_status = RuleStatus.FAILED.value
        elif warning_checks > 0:
            overall_status = RuleStatus.WARNING.value
        else:
            overall_status = RuleStatus.PASSED.value

        # 8. Persist run and findings
        val_run = ValidationRun(
            id=run_id,
            scenario_id=scenario_id,
            fixture_version=scenario.active_fixture_version,
            status=overall_status,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warning_checks=warning_checks,
            skipped_checks=skipped_checks,
            error_checks=error_checks,
            execution_duration_ms=total_duration_ms,
            executed_at=now,
        )

        try:
            db.add(val_run)
            db.add_all(findings)
            db.commit()
            db.refresh(val_run)
        except Exception as exc:
            db.rollback()
            logger.exception("Failed to persist validation run and findings: %s", exc)
            raise LuxException(
                code="PERSISTENCE_ERROR",
                message=f"Failed to persist validation run: {exc}",
                details={"error": str(exc)},
            ) from exc

        return val_run

    @classmethod
    def get_validation_run(cls, run_id: str, db: Session) -> ValidationRun:
        """Fetch validation run by unique identifier."""
        run = db.execute(
            select(ValidationRun).where(ValidationRun.id == run_id)
        ).scalar_one_or_none()
        if not run:
            raise NotFoundError(
                code="VALIDATION_RUN_NOT_FOUND",
                message=f"Validation run '{run_id}' was not found.",
                details={"run_id": run_id},
            )
        return run

    @classmethod
    def list_validation_runs(
        cls,
        db: Session,
        scenario_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[int, list[ValidationRun]]:
        """List validation runs, optionally filtered by scenario ID."""
        base_query = select(ValidationRun)
        count_query = select(func.count(ValidationRun.id))

        if scenario_id:
            base_query = base_query.where(ValidationRun.scenario_id == scenario_id)
            count_query = count_query.where(ValidationRun.scenario_id == scenario_id)

        total = db.execute(count_query).scalar_one() or 0
        runs = (
            db.execute(
                base_query.order_by(ValidationRun.executed_at.desc()).offset(offset).limit(limit)
            )
            .scalars()
            .all()
        )
        return total, list(runs)

    @classmethod
    def list_run_findings(
        cls,
        run_id: str,
        db: Session,
        severity: str | None = None,
        status: str | None = None,
        dataset_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[ValidationFinding]]:
        """Query granular findings for a validation run with optional filtering."""
        # Ensure run exists
        cls.get_validation_run(run_id, db)

        base_query = (
            select(ValidationFinding)
            .options(joinedload(ValidationFinding.rule))
            .where(ValidationFinding.run_id == run_id)
        )
        count_query = select(func.count(ValidationFinding.id)).where(
            ValidationFinding.run_id == run_id
        )

        if severity:
            sev_upper = severity.upper()
            base_query = base_query.where(ValidationFinding.severity == sev_upper)
            count_query = count_query.where(ValidationFinding.severity == sev_upper)

        if status:
            stat_upper = status.upper()
            base_query = base_query.where(ValidationFinding.status == stat_upper)
            count_query = count_query.where(ValidationFinding.status == stat_upper)

        if dataset_id:
            base_query = base_query.where(ValidationFinding.dataset_id == dataset_id)
            count_query = count_query.where(ValidationFinding.dataset_id == dataset_id)

        total_findings = db.execute(count_query).scalar_one() or 0
        findings = (
            db.execute(base_query.order_by(ValidationFinding.id).offset(offset).limit(limit))
            .scalars()
            .all()
        )
        return total_findings, list(findings)
