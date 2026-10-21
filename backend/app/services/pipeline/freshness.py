"""Dataset partition freshness and SLA monitoring service."""

from __future__ import annotations

import csv
import json
import logging
import math
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.pipeline import FreshnessCheck
from app.schemas.pipeline import FreshnessCheckResponse, FreshnessStatus
from app.services.pipeline.service import parse_iso_datetime

logger = logging.getLogger("lux.services.pipeline.freshness")


def _to_utc(dt: datetime | None) -> datetime | None:
    """Normalize datetime to timezone-aware UTC datetime."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class FreshnessService:
    """Service for dataset partition freshness evaluation, SLA monitoring, and persistence."""

    @staticmethod
    def calculate_hours_behind(
        expected_timestamp: datetime,
        observed_timestamp: datetime | None,
        status: str | FreshnessStatus | None = None,
    ) -> float:
        """
        Calculate the hours that an observed partition timestamp is behind SLA expectation.

        Precision logic preserves exact 2-decimal truncation (e.g., Sunday 18:00 vs 23:59:59
        yields 5.99h).

        Args:
            expected_timestamp: Cutoff datetime expected for the dataset partition.
            observed_timestamp: Latest observed transaction or ingestion datetime in the partition.
            status: Optional pre-classified status string.

        Returns:
            Hours behind expectation (float rounded/truncated to 2 decimal places, min 0.0).
        """
        if status in (FreshnessStatus.FRESH, FreshnessStatus.FRESH.value):
            return 0.0

        if observed_timestamp is None:
            return 0.0

        exp_utc = _to_utc(expected_timestamp)
        obs_utc = _to_utc(observed_timestamp)
        if exp_utc is None or obs_utc is None or obs_utc >= exp_utc:
            return 0.0

        diff_seconds = (exp_utc - obs_utc).total_seconds()
        if diff_seconds <= 0:
            return 0.0

        # Truncate to two decimals to match declared SLA convention (21599s -> 5.99h)
        hours = diff_seconds / 3600.0
        return math.floor(hours * 100.0) / 100.0

    @classmethod
    def classify_freshness(
        cls,
        expected_timestamp: datetime,
        observed_timestamp: datetime | None,
        sla_hours: int | float = 24,
        tolerance_seconds: float = 300.0,
    ) -> tuple[FreshnessStatus, float]:
        """
        Classify dataset partition freshness status and compute delay hours.

        Args:
            expected_timestamp: Expected partition cutoff timestamp.
            observed_timestamp: Observed partition timestamp, or None if missing.
            sla_hours: Declared SLA window in hours.
            tolerance_seconds: Grace period in seconds (default: 5 minutes / 300s).

        Returns:
            Tuple of (FreshnessStatus, hours_behind).
        """
        if observed_timestamp is None:
            return FreshnessStatus.MISSING, 0.0

        exp_utc = _to_utc(expected_timestamp)
        obs_utc = _to_utc(observed_timestamp)
        if exp_utc is None or obs_utc is None:
            return FreshnessStatus.MISSING, 0.0

        diff_seconds = (exp_utc - obs_utc).total_seconds()
        if diff_seconds <= tolerance_seconds:
            return FreshnessStatus.FRESH, 0.0

        hours_behind = math.floor((diff_seconds / 3600.0) * 100.0) / 100.0
        return FreshnessStatus.STALE, hours_behind

    @classmethod
    def evaluate_dataset_records(
        cls,
        records: Sequence[dict[str, Any]],
        timestamp_column: str,
        expected_timestamp: datetime,
        sla_hours: int | float = 24,
        tolerance_seconds: float = 300.0,
    ) -> tuple[FreshnessStatus, datetime | None, float]:
        """
        Evaluate dataset freshness directly from an in-memory sequence of record dicts.

        Args:
            records: Sequence of row mappings.
            timestamp_column: Name of the timestamp column to evaluate.
            expected_timestamp: Expected partition cutoff timestamp.
            sla_hours: Declared SLA window in hours.
            tolerance_seconds: Grace period in seconds.

        Returns:
            Tuple of (FreshnessStatus, max_observed_timestamp, hours_behind).
        """
        if not records:
            return FreshnessStatus.MISSING, None, 0.0

        parsed_timestamps: list[datetime] = []
        for row in records:
            raw_val = row.get(timestamp_column)
            if raw_val is not None:
                if isinstance(raw_val, datetime):
                    parsed_timestamps.append(_to_utc(raw_val) or raw_val)
                elif isinstance(raw_val, str) and raw_val.strip():
                    dt = parse_iso_datetime(raw_val.strip())
                    if dt is not None:
                        parsed_timestamps.append(_to_utc(dt) or dt)

        if not parsed_timestamps:
            return FreshnessStatus.MISSING, None, 0.0

        max_observed = max(parsed_timestamps)
        status, hours_behind = cls.classify_freshness(
            expected_timestamp=expected_timestamp,
            observed_timestamp=max_observed,
            sla_hours=sla_hours,
            tolerance_seconds=tolerance_seconds,
        )
        return status, max_observed, hours_behind

    @classmethod
    def evaluate_dataset_file(
        cls,
        file_path: Path,
        timestamp_column: str,
        expected_timestamp: datetime,
        sla_hours: int | float = 24,
        file_format: str = "csv",
        tolerance_seconds: float = 300.0,
    ) -> tuple[FreshnessStatus, datetime | None, float]:
        """
        Evaluate dataset freshness directly from a local CSV or JSON file.

        Args:
            file_path: Filesystem path to dataset.
            timestamp_column: Name of the timestamp column.
            expected_timestamp: Expected partition cutoff timestamp.
            sla_hours: Declared SLA window in hours.
            file_format: Format ('csv' or 'json').
            tolerance_seconds: Grace period in seconds.

        Returns:
            Tuple of (FreshnessStatus, max_observed_timestamp, hours_behind).
        """
        if not file_path.exists() or not file_path.is_file():
            logger.warning("Dataset file '%s' does not exist for freshness evaluation.", file_path)
            return FreshnessStatus.MISSING, None, 0.0

        records: list[dict[str, Any]] = []
        try:
            if file_format.lower() == "csv" or file_path.suffix.lower() == ".csv":
                with open(file_path, encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    records = list(reader)
            elif file_format.lower() == "json" or file_path.suffix.lower() == ".json":
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        records = data
                    elif isinstance(data, dict):
                        records = [data]
        except Exception as exc:
            logger.exception("Failed to read dataset file %s: %s", file_path, exc)
            return FreshnessStatus.MISSING, None, 0.0

        return cls.evaluate_dataset_records(
            records=records,
            timestamp_column=timestamp_column,
            expected_timestamp=expected_timestamp,
            sla_hours=sla_hours,
            tolerance_seconds=tolerance_seconds,
        )

    @classmethod
    def get_freshness_status(
        cls,
        db: Session,
        scenario_id: str | None = None,
        dataset_id: str | None = None,
    ) -> list[FreshnessCheckResponse]:
        """
        Retrieve dataset partition freshness checkpoints for a scenario and/or dataset.

        Args:
            db: Active SQLAlchemy database session.
            scenario_id: Optional scenario identifier filter.
            dataset_id: Optional dataset identifier filter.

        Returns:
            List of FreshnessCheckResponse schemas.
        """
        query = select(FreshnessCheck).options(joinedload(FreshnessCheck.dataset))
        if scenario_id:
            query = query.where(FreshnessCheck.scenario_id == scenario_id)
        if dataset_id:
            query = query.where(FreshnessCheck.dataset_id == dataset_id)

        query = query.order_by(FreshnessCheck.dataset_id.asc(), FreshnessCheck.checked_at.desc())
        checks = db.execute(query).scalars().all()

        results: list[FreshnessCheckResponse] = []
        for check in checks:
            dataset_name = (
                check.dataset.name
                if check.dataset is not None and check.dataset.name
                else f"{check.dataset_id}.csv"
            )

            # Determine status classification
            raw_status = (check.status or "").upper()
            is_missing = (
                raw_status == FreshnessStatus.MISSING.value
                or check.observed_partition_timestamp is None
            )
            if is_missing:
                status = FreshnessStatus.MISSING
                hours_behind = 0.0
            elif raw_status == FreshnessStatus.FRESH.value:
                status = FreshnessStatus.FRESH
                hours_behind = 0.0
            else:
                status = FreshnessStatus.STALE
                hours_behind = cls.calculate_hours_behind(
                    expected_timestamp=check.expected_partition_timestamp,
                    observed_timestamp=check.observed_partition_timestamp,
                    status=status,
                )

            results.append(
                FreshnessCheckResponse(
                    id=check.id,
                    scenario_id=check.scenario_id,
                    dataset_id=check.dataset_id,
                    dataset_name=dataset_name,
                    sla_hours=check.sla_hours,
                    expected_partition_timestamp=check.expected_partition_timestamp,
                    observed_partition_timestamp=check.observed_partition_timestamp,
                    status=status,
                    hours_behind=hours_behind,
                    checked_at=check.checked_at,
                )
            )

        return results

    @classmethod
    def seed_freshness_checks(
        cls,
        db: Session,
        scenario_id: str,
        checks_data: list[dict[str, Any]],
        loaded_datasets: Sequence[str] | set[str] | None = None,
    ) -> list[FreshnessCheck]:
        """
        Seed or update freshness checkpoint records for a scenario from definitions.

        Args:
            db: Active SQLAlchemy database session.
            scenario_id: Target scenario identifier.
            checks_data: List of freshness check definition dictionaries.
            loaded_datasets: Optional filter collection of valid dataset IDs.

        Returns:
            List of persisted FreshnessCheck models.
        """
        now = datetime.now(UTC)
        persisted: list[FreshnessCheck] = []

        for check_def in checks_data:
            check_id = check_def["id"]
            dataset_id = check_def["dataset_id"]
            if loaded_datasets is not None and dataset_id not in loaded_datasets:
                continue

            exp_dt = parse_iso_datetime(check_def.get("expected_partition_timestamp")) or now
            obs_dt = parse_iso_datetime(check_def.get("observed_partition_timestamp"))
            chk_dt = parse_iso_datetime(check_def.get("checked_at")) or now
            sla = int(check_def.get("sla_hours", 24))
            raw_status = check_def.get("status")

            if raw_status:
                check_status = str(raw_status).upper()
            else:
                classified_status, _ = cls.classify_freshness(
                    expected_timestamp=exp_dt,
                    observed_timestamp=obs_dt,
                    sla_hours=sla,
                )
                check_status = classified_status.value

            existing = db.execute(
                select(FreshnessCheck).where(FreshnessCheck.id == check_id)
            ).scalar_one_or_none()

            if existing:
                existing.scenario_id = scenario_id
                existing.dataset_id = dataset_id
                existing.expected_partition_timestamp = exp_dt
                existing.observed_partition_timestamp = obs_dt
                existing.sla_hours = sla
                existing.status = check_status
                existing.checked_at = chk_dt
                persisted.append(existing)
            else:
                fresh_check = FreshnessCheck(
                    id=check_id,
                    scenario_id=scenario_id,
                    dataset_id=dataset_id,
                    expected_partition_timestamp=exp_dt,
                    observed_partition_timestamp=obs_dt,
                    sla_hours=sla,
                    status=check_status,
                    checked_at=chk_dt,
                )
                db.add(fresh_check)
                persisted.append(fresh_check)

        db.flush()
        return persisted
