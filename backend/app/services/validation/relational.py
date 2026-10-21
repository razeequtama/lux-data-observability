"""Relational, temporal, schema, and freshness data quality rule evaluators."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from app.schemas.validation import (
    RuleEvaluationResult,
    RuleStatus,
)
from app.services.validation.base import BaseValidationRule, ValidationContext


def _parse_timestamp(val: Any) -> datetime | None:
    """Safely parse a value into a UTC-aware datetime object."""
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=UTC)
        return val.astimezone(UTC)
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day, tzinfo=UTC)
    if isinstance(val, str):
        clean = val.strip()
        if not clean:
            return None
        # Replace trailing Z with UTC offset for ISO compatibility
        clean = clean.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(clean)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=UTC)
            return dt.astimezone(UTC)
        except (ValueError, TypeError):
            return None
    return None


class ReferentialIntegrityRule(BaseValidationRule):
    """Rule evaluator verifying foreign key references exist in a parent dataset."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Target/child column(s)
        if "column" in self.parameters:
            col_param = self.parameters["column"]
            self.columns: list[str] = (
                [str(c) for c in col_param] if isinstance(col_param, list) else [str(col_param)]
            )
        elif "columns" in self.parameters:
            self.columns = [str(c) for c in self.parameters["columns"]]
        else:
            raise ValueError("ReferentialIntegrityRule requires 'column' parameter.")

        # Parent dataset and column(s)
        self.parent_dataset: str = str(
            self.parameters.get("parent_dataset") or self.parameters.get("referenced_dataset") or ""
        )
        if not self.parent_dataset:
            raise ValueError("ReferentialIntegrityRule requires 'parent_dataset' parameter.")

        if "parent_column" in self.parameters:
            p_col_param = self.parameters["parent_column"]
            self.parent_columns: list[str] = (
                [str(c) for c in p_col_param]
                if isinstance(p_col_param, list)
                else [str(p_col_param)]
            )
        elif "parent_columns" in self.parameters:
            self.parent_columns = [str(c) for c in self.parameters["parent_columns"]]
        elif "referenced_column" in self.parameters:
            ref_col = self.parameters["referenced_column"]
            self.parent_columns = (
                [str(c) for c in ref_col] if isinstance(ref_col, list) else [str(ref_col)]
            )
        else:
            # Default to same column name(s) if not specified
            self.parent_columns = self.columns

        if len(self.columns) != len(self.parent_columns):
            raise ValueError(
                f"ReferentialIntegrityRule column count ({len(self.columns)}) "
                f"must match parent_columns count ({len(self.parent_columns)})."
            )

        self.allow_null: bool = bool(self.parameters.get("allow_null", False))

    def _extract_key(self, row: dict[str, Any], cols: list[str]) -> tuple[str, ...] | None:
        """Extract a tuple key from a row. Returns None if required item is null and allowed."""
        values: list[str] = []
        has_null = False
        for col in cols:
            val = row.get(col)
            if val is None or (isinstance(val, str) and not val.strip()):
                has_null = True
                values.append("")
            else:
                values.append(str(val).strip())

        if has_null and self.allow_null:
            return None
        return tuple(values)

    def _evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
        # Retrieve parent dataset records
        parent_records_iter = context.get_dataset_records(self.parent_dataset)
        parent_keys: set[tuple[str, ...]] = set()

        parent_count = 0
        for row in parent_records_iter:
            parent_count += 1
            key = self._extract_key(row, self.parent_columns)
            if key is not None and any(key):
                parent_keys.add(key)

        if parent_count == 0 and not parent_keys:
            return self._build_result(
                status=RuleStatus.ERROR,
                affected_fields=self.columns,
                affected_record_count=0,
                total_record_count=context.get_record_count(),
                message=(
                    f"Parent dataset '{self.parent_dataset}' could not be resolved or "
                    "contains 0 records."
                ),
                evidence={
                    "parent_dataset": self.parent_dataset,
                    "parent_columns": self.parent_columns,
                    "reason": "Parent dataset is empty or missing from context",
                },
            )

        total_records = 0
        orphaned_keys: set[str] = set()
        sample_violations: list[dict[str, Any]] = []
        affected_count = 0

        for idx, row in enumerate(context.get_records()):
            total_records += 1
            key = self._extract_key(row, self.columns)

            if key is None:
                # Null foreign key allowed
                continue

            if key not in parent_keys:
                affected_count += 1
                key_display = key[0] if len(key) == 1 else str(key)
                orphaned_keys.add(key_display)

                if len(sample_violations) < 50:
                    sample_violations.append(
                        {
                            "row_index": idx,
                            "foreign_key_value": key_display,
                            "parent_dataset": self.parent_dataset,
                            "parent_column": ", ".join(self.parent_columns),
                            "row_sample": {
                                col: row.get(col)
                                for col in (self.columns + ["item_id", "id", "order_id"])
                                if col in row
                            },
                        }
                    )

        cols_str = ", ".join(self.columns)
        parent_cols_str = ", ".join(self.parent_columns)

        if affected_count > 0:
            return self._build_result(
                status=RuleStatus.FAILED,
                affected_fields=self.columns,
                affected_record_count=affected_count,
                total_record_count=total_records,
                message=(
                    f"Found {affected_count} orphaned record(s) in "
                    f"'{self.dataset_id}.{cols_str}' missing from parent dataset "
                    f"'{self.parent_dataset}.{parent_cols_str}'."
                ),
                evidence={
                    "parent_dataset": self.parent_dataset,
                    "parent_columns": self.parent_columns,
                    "parent_key_count": len(parent_keys),
                    "total_orphaned_records": affected_count,
                    "sample_orphaned_keys": sorted(orphaned_keys)[:25],
                    "sample_violations": sample_violations,
                },
            )

        return self._build_result(
            status=RuleStatus.PASSED,
            affected_fields=self.columns,
            affected_record_count=0,
            total_record_count=total_records,
            message=(
                f"All {total_records} records in '{self.dataset_id}.{cols_str}' "
                f"satisfy referential integrity against "
                f"'{self.parent_dataset}.{parent_cols_str}'."
            ),
            evidence={
                "parent_dataset": self.parent_dataset,
                "parent_columns": self.parent_columns,
                "parent_key_count": len(parent_keys),
            },
        )


class TemporalAnomalyRule(BaseValidationRule):
    """Rule evaluator for timestamp parsing, future dates, bounds, and temporal gaps."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if "column" not in self.parameters:
            raise ValueError("TemporalAnomalyRule requires 'column' parameter.")
        self.column: str = str(self.parameters["column"])
        self.allow_future: bool = bool(self.parameters.get("allow_future", False))
        self.allow_null: bool = bool(self.parameters.get("allow_null", False))

        # Configurable reference time for deterministic testing
        now_param = self.parameters.get("now_reference") or self.parameters.get("reference_time")
        self.now_reference: datetime | None = _parse_timestamp(now_param) if now_param else None

        # Min/max allowable timestamp bounds
        min_param = self.parameters.get("min_date") or self.parameters.get("min_timestamp")
        self.min_date: datetime | None = _parse_timestamp(min_param) if min_param else None

        max_param = self.parameters.get("max_date") or self.parameters.get("max_timestamp")
        self.max_date: datetime | None = _parse_timestamp(max_param) if max_param else None

        # Temporal gap detection threshold in hours
        gap_param = self.parameters.get("max_gap_hours")
        self.max_gap_hours: float | None = float(gap_param) if gap_param is not None else None

    def _evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
        now_dt = self.now_reference or datetime.now(UTC)

        total_records = 0
        unparseable_records: list[dict[str, Any]] = []
        future_records: list[dict[str, Any]] = []
        out_of_range_records: list[dict[str, Any]] = []
        null_records: list[dict[str, Any]] = []
        valid_timestamps: list[tuple[datetime, int, dict[str, Any]]] = []

        for idx, row in enumerate(context.get_records()):
            total_records += 1
            raw_val = row.get(self.column)

            if raw_val is None or (isinstance(raw_val, str) and not raw_val.strip()):
                if not self.allow_null:
                    if len(null_records) < 20:
                        null_records.append({"row_index": idx, "value": raw_val})
                continue

            parsed_dt = _parse_timestamp(raw_val)
            if parsed_dt is None:
                if len(unparseable_records) < 20:
                    unparseable_records.append({"row_index": idx, "value": str(raw_val)})
                continue

            # Check future dates
            if not self.allow_future and parsed_dt > now_dt:
                if len(future_records) < 20:
                    future_records.append(
                        {
                            "row_index": idx,
                            "observed_timestamp": parsed_dt.isoformat(),
                            "reference_now": now_dt.isoformat(),
                        }
                    )

            # Check min/max bounds
            if self.min_date and parsed_dt < self.min_date:
                if len(out_of_range_records) < 20:
                    out_of_range_records.append(
                        {
                            "row_index": idx,
                            "observed_timestamp": parsed_dt.isoformat(),
                            "bound": "min_date",
                            "limit": self.min_date.isoformat(),
                        }
                    )
            elif self.max_date and parsed_dt > self.max_date:
                if len(out_of_range_records) < 20:
                    out_of_range_records.append(
                        {
                            "row_index": idx,
                            "observed_timestamp": parsed_dt.isoformat(),
                            "bound": "max_date",
                            "limit": self.max_date.isoformat(),
                        }
                    )

            valid_timestamps.append((parsed_dt, idx, row))

        # Detect temporal gaps if requested
        detected_gaps: list[dict[str, Any]] = []
        max_observed_gap_hours = 0.0

        if self.max_gap_hours is not None and len(valid_timestamps) >= 2:
            # Sort chronologically by datetime
            valid_timestamps.sort(key=lambda item: item[0])

            for i in range(len(valid_timestamps) - 1):
                dt_curr, idx_curr, _ = valid_timestamps[i]
                dt_next, idx_next, _ = valid_timestamps[i + 1]
                gap_hours = (dt_next - dt_curr).total_seconds() / 3600.0
                if gap_hours > max_observed_gap_hours:
                    max_observed_gap_hours = gap_hours

                if gap_hours > self.max_gap_hours:
                    detected_gaps.append(
                        {
                            "gap_start": dt_curr.isoformat(),
                            "gap_end": dt_next.isoformat(),
                            "gap_hours": round(gap_hours, 2),
                            "max_allowed_hours": self.max_gap_hours,
                            "preceding_row_index": idx_curr,
                            "succeeding_row_index": idx_next,
                        }
                    )

        total_violations = (
            len(unparseable_records)
            + len(future_records)
            + len(out_of_range_records)
            + len(null_records)
            + len(detected_gaps)
        )

        if total_violations > 0:
            reasons: list[str] = []
            if detected_gaps:
                reasons.append(
                    f"{len(detected_gaps)} temporal gap(s) exceeding "
                    f"{self.max_gap_hours}h threshold (max gap: {max_observed_gap_hours:.2f}h)"
                )
            if future_records:
                reasons.append(f"{len(future_records)} future timestamp(s)")
            if unparseable_records:
                reasons.append(f"{len(unparseable_records)} unparseable timestamp(s)")
            if out_of_range_records:
                reasons.append(f"{len(out_of_range_records)} out-of-range timestamp(s)")
            if null_records:
                reasons.append(f"{len(null_records)} null timestamp(s)")

            message = (
                f"Detected temporal anomalies in '{self.dataset_id}.{self.column}': "
                f"{'; '.join(reasons)}."
            )

            return self._build_result(
                status=RuleStatus.FAILED,
                affected_fields=[self.column],
                affected_record_count=total_violations,
                total_record_count=total_records,
                message=message,
                evidence={
                    "column": self.column,
                    "temporal_gaps": detected_gaps,
                    "max_observed_gap_hours": round(max_observed_gap_hours, 2),
                    "sample_future_records": future_records,
                    "sample_unparseable_records": unparseable_records,
                    "sample_out_of_range_records": out_of_range_records,
                    "sample_null_records": null_records,
                },
            )

        min_ts = valid_timestamps[0][0].isoformat() if valid_timestamps else None
        max_ts = valid_timestamps[-1][0].isoformat() if valid_timestamps else None

        return self._build_result(
            status=RuleStatus.PASSED,
            affected_fields=[self.column],
            affected_record_count=0,
            total_record_count=total_records,
            message=(
                f"All {total_records} records in '{self.dataset_id}.{self.column}' "
                "passed temporal anomaly checks."
            ),
            evidence={
                "column": self.column,
                "min_observed_timestamp": min_ts,
                "max_observed_timestamp": max_ts,
                "max_observed_gap_hours": (
                    round(max_observed_gap_hours, 2) if self.max_gap_hours is not None else None
                ),
            },
        )


class SchemaIntegrityRule(BaseValidationRule):
    """Rule evaluator verifying column existence, column counts, and data type drift."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        raw_cols = self.parameters.get("expected_columns") or self.parameters.get("columns")
        if not raw_cols:
            raise ValueError("SchemaIntegrityRule requires 'expected_columns' parameter.")

        self.expected_column_names: list[str] = []
        self.expected_types: dict[str, str] = {}

        if isinstance(raw_cols, list):
            for item in raw_cols:
                if isinstance(item, dict):
                    col_name = str(item.get("name", ""))
                    self.expected_column_names.append(col_name)
                    if "type" in item:
                        self.expected_types[col_name] = str(item["type"]).lower()
                else:
                    self.expected_column_names.append(str(item))
        elif isinstance(raw_cols, dict):
            for col_name, col_type in raw_cols.items():
                self.expected_column_names.append(str(col_name))
                self.expected_types[str(col_name)] = str(col_type).lower()

        # Merge with explicit expected_types if provided
        if "expected_types" in self.parameters and isinstance(
            self.parameters["expected_types"], dict
        ):
            for k, v in self.parameters["expected_types"].items():
                self.expected_types[str(k)] = str(v).lower()

        self.allow_extra_columns: bool = bool(self.parameters.get("allow_extra_columns", True))
        self.strict_order: bool = bool(self.parameters.get("strict_order", False))

    def _check_type_conformity(self, val: Any, expected_type: str) -> bool:
        """Check whether a value conforms to an expected data type."""
        if val is None or (isinstance(val, str) and not val.strip()):
            return True  # Nullability is validated separately by NullCheckRule

        exp = expected_type.lower()
        if exp in ("integer", "int"):
            try:
                int(str(val).strip())
                return True
            except (ValueError, TypeError):
                return False
        elif exp in ("float", "number", "decimal"):
            try:
                float(str(val).strip())
                return True
            except (ValueError, TypeError):
                return False
        elif exp in ("boolean", "bool"):
            return str(val).strip().lower() in ("true", "false", "1", "0", "t", "f", "yes", "no")
        elif exp in ("timestamp", "datetime", "date"):
            return _parse_timestamp(val) is not None
        elif exp in ("string", "text", "str"):
            return True
        return True

    def _evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
        records = context.get_records_as_list()
        total_records = len(records)

        observed_columns: list[str] = []
        if records:
            observed_columns = list(records[0].keys())

        missing_columns = [col for col in self.expected_column_names if col not in observed_columns]
        unexpected_columns = (
            [col for col in observed_columns if col not in self.expected_column_names]
            if not self.allow_extra_columns
            else []
        )

        order_mismatch = False
        if self.strict_order and len(observed_columns) >= len(self.expected_column_names):
            if observed_columns[: len(self.expected_column_names)] != self.expected_column_names:
                order_mismatch = True

        # Check type drift across sample records
        type_mismatches: list[dict[str, Any]] = []
        if self.expected_types and records:
            sample_size = min(len(records), 100)
            for idx in range(sample_size):
                row = records[idx]
                for col, exp_type in self.expected_types.items():
                    if col in row:
                        val = row[col]
                        if not self._check_type_conformity(val, exp_type):
                            if len(type_mismatches) < 20:
                                type_mismatches.append(
                                    {
                                        "row_index": idx,
                                        "column": col,
                                        "expected_type": exp_type,
                                        "observed_value": str(val),
                                    }
                                )

        failures: list[str] = []
        if missing_columns:
            failures.append(
                f"missing {len(missing_columns)} column(s): {', '.join(missing_columns)}"
            )
        if unexpected_columns:
            failures.append(
                f"found {len(unexpected_columns)} unexpected column(s): "
                f"{', '.join(unexpected_columns)}"
            )
        if order_mismatch:
            failures.append("column ordering does not match strict expected schema")
        if type_mismatches:
            failures.append(f"{len(type_mismatches)} type drift violation(s) in sample rows")

        if failures:
            affected_count = len(missing_columns) + len(unexpected_columns) + len(type_mismatches)
            msg = f"Schema integrity violations in '{self.dataset_id}': {'; '.join(failures)}."
            return self._build_result(
                status=RuleStatus.FAILED,
                affected_fields=missing_columns or self.expected_column_names,
                affected_record_count=affected_count,
                total_record_count=total_records,
                message=msg,
                evidence={
                    "observed_columns": observed_columns,
                    "expected_columns": self.expected_column_names,
                    "missing_columns": missing_columns,
                    "unexpected_columns": unexpected_columns,
                    "type_mismatches": type_mismatches,
                },
            )

        return self._build_result(
            status=RuleStatus.PASSED,
            affected_fields=self.expected_column_names,
            affected_record_count=0,
            total_record_count=total_records,
            message=(
                f"Dataset '{self.dataset_id}' satisfies schema integrity requirements "
                f"({len(observed_columns)} column(s) verified)."
            ),
            evidence={
                "observed_columns": observed_columns,
                "expected_columns": self.expected_column_names,
            },
        )


class FreshnessRule(BaseValidationRule):
    """Rule evaluator for partition timestamp recency vs SLA and continuity."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if "column" not in self.parameters:
            raise ValueError("FreshnessRule requires 'column' parameter.")
        self.column: str = str(self.parameters["column"])

        sla_param = self.parameters.get("sla_hours", 24)
        self.sla_hours: float = float(sla_param)

        gap_param = self.parameters.get("max_gap_hours")
        self.max_gap_hours: float | None = float(gap_param) if gap_param is not None else None

        # Reference time for partition check
        ref_param = (
            self.parameters.get("expected_partition_timestamp")
            or self.parameters.get("as_of")
            or self.parameters.get("now_reference")
        )
        self.reference_timestamp: datetime | None = (
            _parse_timestamp(ref_param) if ref_param else None
        )

        self.warn_only: bool = bool(self.parameters.get("warn_only", False))

    def _evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
        total_records = 0
        timestamps: list[tuple[datetime, int]] = []

        for idx, row in enumerate(context.get_records()):
            total_records += 1
            raw_val = row.get(self.column)
            dt = _parse_timestamp(raw_val)
            if dt is not None:
                timestamps.append((dt, idx))

        if not timestamps:
            return self._build_result(
                status=RuleStatus.FAILED,
                affected_fields=[self.column],
                affected_record_count=total_records,
                total_record_count=total_records,
                message=(
                    f"Freshness check failed: no valid timestamps found in "
                    f"'{self.dataset_id}.{self.column}'."
                ),
                evidence={"column": self.column, "status": "MISSING"},
            )

        timestamps.sort(key=lambda t: t[0])
        observed_max_dt = timestamps[-1][0]
        observed_min_dt = timestamps[0][0]

        # Calculate SLA delay if reference timestamp is available
        ref_dt = self.reference_timestamp or datetime.now(UTC)
        hours_behind = max(0.0, (ref_dt - observed_max_dt).total_seconds() / 3600.0)

        # Check gap violations if max_gap_hours is configured
        max_observed_gap_hours = 0.0
        gap_violations: list[dict[str, Any]] = []

        if self.max_gap_hours is not None and len(timestamps) >= 2:
            for i in range(len(timestamps) - 1):
                t1, idx1 = timestamps[i]
                t2, idx2 = timestamps[i + 1]
                gap = (t2 - t1).total_seconds() / 3600.0
                if gap > max_observed_gap_hours:
                    max_observed_gap_hours = gap

                if gap > self.max_gap_hours:
                    gap_violations.append(
                        {
                            "gap_start": t1.isoformat(),
                            "gap_end": t2.isoformat(),
                            "gap_hours": round(gap, 2),
                            "max_allowed_hours": self.max_gap_hours,
                            "preceding_row_index": idx1,
                            "succeeding_row_index": idx2,
                        }
                    )

        sla_breached = self.reference_timestamp is not None and hours_behind > self.sla_hours
        gap_breached = len(gap_violations) > 0

        if sla_breached or gap_breached:
            status = RuleStatus.WARNING if self.warn_only else RuleStatus.FAILED
            issues: list[str] = []
            if sla_breached:
                issues.append(
                    f"partition is {hours_behind:.2f} hours behind expected timestamp "
                    f"(SLA: {self.sla_hours:.1f}h)"
                )
            if gap_breached:
                issues.append(
                    f"detected {len(gap_violations)} transaction window gap(s) exceeding "
                    f"{self.max_gap_hours}h (max gap: {max_observed_gap_hours:.2f}h)"
                )

            message = (
                f"Partition freshness violation in '{self.dataset_id}.{self.column}': "
                f"{'; '.join(issues)}."
            )
            affected_count = len(gap_violations) if gap_breached else 1

            return self._build_result(
                status=status,
                affected_fields=[self.column],
                affected_record_count=affected_count,
                total_record_count=total_records,
                message=message,
                evidence={
                    "column": self.column,
                    "sla_hours": self.sla_hours,
                    "max_gap_hours": self.max_gap_hours,
                    "observed_latest_timestamp": observed_max_dt.isoformat(),
                    "expected_partition_timestamp": (
                        ref_dt.isoformat() if self.reference_timestamp else None
                    ),
                    "hours_behind": round(hours_behind, 2) if self.reference_timestamp else None,
                    "observed_max_gap_hours": round(max_observed_gap_hours, 2),
                    "gap_violations": gap_violations,
                    "status": "STALE",
                },
            )

        return self._build_result(
            status=RuleStatus.PASSED,
            affected_fields=[self.column],
            affected_record_count=0,
            total_record_count=total_records,
            message=(
                f"Partition freshness check passed for '{self.dataset_id}.{self.column}'. "
                f"Latest record ({observed_max_dt.isoformat()}) satisfies freshness criteria."
            ),
            evidence={
                "column": self.column,
                "sla_hours": self.sla_hours,
                "observed_latest_timestamp": observed_max_dt.isoformat(),
                "observed_earliest_timestamp": observed_min_dt.isoformat(),
                "observed_max_gap_hours": (
                    round(max_observed_gap_hours, 2) if self.max_gap_hours is not None else None
                ),
                "status": "FRESH",
            },
        )
