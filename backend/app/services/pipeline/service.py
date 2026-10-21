"""Pipeline history service for managing execution runs and dual-dimension status tracking."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.pipeline import PipelineRun
from app.schemas.pipeline import (
    PipelineExecutionStatus,
    QualityHealthStatus,
)
from app.schemas.validation import RuleSeverity, RuleStatus

logger = logging.getLogger("lux.services.pipeline")


def parse_iso_datetime(val: str | None) -> datetime | None:
    """Parse ISO formatted datetime string safely into a UTC datetime object."""
    if not val:
        return None
    try:
        clean = val.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception:
        return None


class PipelineHistoryService:
    """Service managing pipeline run persistence, history, and dual-dimension tracking."""

    @staticmethod
    def get_runs(
        db: Session,
        scenario_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PipelineRun]:
        """
        Retrieve historical pipeline execution runs sorted descending by start_time.

        Args:
            db: Active SQLAlchemy database session.
            scenario_id: Optional scenario identifier filter.
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            List of PipelineRun domain models.
        """
        query = select(PipelineRun)
        if scenario_id:
            query = query.where(PipelineRun.scenario_id == scenario_id)
        query = query.order_by(PipelineRun.start_time.desc(), PipelineRun.created_at.desc())
        if offset > 0:
            query = query.offset(offset)
        query = query.limit(limit)
        return list(db.execute(query).scalars().all())

    @staticmethod
    def get_run_by_id(
        db: Session,
        run_id: str,
    ) -> PipelineRun:
        """
        Retrieve a single pipeline run by its unique identifier.

        Args:
            db: Active SQLAlchemy database session.
            run_id: Unique pipeline run identifier.

        Returns:
            PipelineRun domain model.

        Raises:
            NotFoundError: If the pipeline run does not exist.
        """
        run = db.execute(select(PipelineRun).where(PipelineRun.id == run_id)).scalar_one_or_none()
        if not run:
            raise NotFoundError(
                code="PIPELINE_RUN_NOT_FOUND",
                message=f"Pipeline run '{run_id}' was not found.",
                details={"run_id": run_id},
            )
        return run

    @staticmethod
    def evaluate_quality_health(
        findings: Sequence[Any] | None = None,
        total_checks_evaluated: int = 0,
    ) -> QualityHealthStatus:
        """
        Evaluate Data Quality Dimension status according to ADR-006 rules:

        1. UNVALIDATED: No checks evaluated.
        2. CORRUPTED: Critical severity failures observed (e.g., duplicate PKs, broken FKs).
        3. DEGRADED: High severity anomalies observed.
        4. WARNING: Low/Medium severity anomalies or warnings observed.
        5. HEALTHY: All executed checks passed.

        Args:
            findings: Iterable of ValidationFinding models, dictionaries, or finding results.
            total_checks_evaluated: Total count of validation checks evaluated.

        Returns:
            QualityHealthStatus enum value.
        """
        if total_checks_evaluated == 0 and not findings:
            return QualityHealthStatus.UNVALIDATED

        if not findings:
            return QualityHealthStatus.HEALTHY

        has_critical = False
        has_high = False
        has_warning_or_low_medium = False

        for f in findings:
            status_val = getattr(f, "status", None) if not isinstance(f, dict) else f.get("status")
            severity_val = (
                getattr(f, "severity", None) if not isinstance(f, dict) else f.get("severity")
            )

            status_str = (
                status_val.value
                if status_val is not None and hasattr(status_val, "value")
                else str(status_val or "").upper()
            )
            severity_str = (
                severity_val.value
                if severity_val is not None and hasattr(severity_val, "value")
                else str(severity_val or "").upper()
            )

            is_failing = status_str in (RuleStatus.FAILED.value, RuleStatus.ERROR.value)
            is_warning_status = status_str == RuleStatus.WARNING.value

            if is_failing:
                if severity_str == RuleSeverity.CRITICAL.value:
                    has_critical = True
                elif severity_str == RuleSeverity.HIGH.value:
                    has_high = True
                elif severity_str in (
                    RuleSeverity.MEDIUM.value,
                    RuleSeverity.LOW.value,
                    RuleSeverity.INFO.value,
                ):
                    has_warning_or_low_medium = True
            elif is_warning_status:
                has_warning_or_low_medium = True

        if has_critical:
            return QualityHealthStatus.CORRUPTED
        if has_high:
            return QualityHealthStatus.DEGRADED
        if has_warning_or_low_medium:
            return QualityHealthStatus.WARNING

        return QualityHealthStatus.HEALTHY

    @staticmethod
    def seed_pipeline_runs(
        db: Session,
        scenario_id: str,
        runs_data: list[dict[str, Any]],
    ) -> list[PipelineRun]:
        """
        Seed or update pipeline run records for a scenario from definitions.

        Args:
            db: Active SQLAlchemy database session.
            scenario_id: Target scenario identifier.
            runs_data: List of pipeline run definition dictionaries.

        Returns:
            List of persisted PipelineRun models.
        """
        now = datetime.now(UTC)
        persisted_runs: list[PipelineRun] = []

        for run_def in runs_data:
            run_id = run_def["id"]
            start_dt = parse_iso_datetime(run_def.get("start_time")) or now
            end_dt = parse_iso_datetime(run_def.get("end_time")) or now

            raw_logs = run_def.get("run_log")
            run_log_str: str | None = None
            if raw_logs is not None:
                if isinstance(raw_logs, str):
                    run_log_str = raw_logs
                else:
                    run_log_str = json.dumps(raw_logs)

            existing_run = db.execute(
                select(PipelineRun).where(PipelineRun.id == run_id)
            ).scalar_one_or_none()

            exec_status = run_def.get(
                "execution_status", PipelineExecutionStatus.COMPLETED_SUCCESS.value
            )
            qual_health = run_def.get("quality_health", QualityHealthStatus.HEALTHY.value)

            if existing_run:
                existing_run.scenario_id = scenario_id
                existing_run.pipeline_name = run_def.get(
                    "pipeline_name", existing_run.pipeline_name
                )
                existing_run.execution_status = exec_status
                existing_run.quality_health = qual_health
                existing_run.start_time = start_dt
                existing_run.end_time = end_dt
                existing_run.duration_ms = run_def.get("duration_ms", existing_run.duration_ms)
                existing_run.records_ingested = run_def.get(
                    "records_ingested", existing_run.records_ingested
                )
                existing_run.records_written = run_def.get(
                    "records_written", existing_run.records_written
                )
                existing_run.error_message = run_def.get("error_message")
                existing_run.run_log = run_log_str
                persisted_runs.append(existing_run)
            else:
                new_run = PipelineRun(
                    id=run_id,
                    scenario_id=scenario_id,
                    pipeline_name=run_def.get("pipeline_name", "default_pipeline"),
                    execution_status=exec_status,
                    quality_health=qual_health,
                    start_time=start_dt,
                    end_time=end_dt,
                    duration_ms=run_def.get("duration_ms", 0),
                    records_ingested=run_def.get("records_ingested", 0),
                    records_written=run_def.get("records_written", 0),
                    error_message=run_def.get("error_message"),
                    run_log=run_log_str,
                    created_at=now,
                )
                db.add(new_run)
                persisted_runs.append(new_run)

        db.flush()
        return persisted_runs

    @classmethod
    def seed_from_scenario_file(
        cls,
        db: Session,
        scenario_id: str,
        file_path: Path,
    ) -> list[PipelineRun]:
        """
        Load pipeline runs from a JSON history file and seed them into the database.

        Args:
            db: Active SQLAlchemy database session.
            scenario_id: Scenario identifier.
            file_path: Path to pipeline_history.json file.

        Returns:
            List of persisted PipelineRun instances.
        """
        if not file_path.exists():
            logger.warning("Pipeline history file '%s' does not exist.", file_path)
            return []

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            runs_data = data.get("pipeline_runs", [])
            return cls.seed_pipeline_runs(db=db, scenario_id=scenario_id, runs_data=runs_data)
        except Exception as exc:
            logger.exception("Failed to seed pipeline runs from file %s: %s", file_path, exc)
            return []
