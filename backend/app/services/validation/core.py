"""Core data quality rule evaluators: nulls, uniqueness, types, record count, and value ranges."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from app.schemas.validation import (
    RuleEvaluationResult,
    RuleStatus,
)
from app.services.validation.base import BaseValidationRule, ValidationContext


class NullCheckRule(BaseValidationRule):
    """Rule evaluator verifying mandatory fields do not contain nulls, blanks, or whitespace."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.columns: list[str] = []
        if "columns" in self.parameters:
            self.columns = list(self.parameters["columns"])
        elif "column" in self.parameters:
            self.columns = [str(self.parameters["column"])]
        else:
            raise ValueError("NullCheckRule requires 'column' or 'columns' parameter.")

    def _is_null_or_blank(self, val: Any) -> bool:
        """Check if a value is None, empty string, or whitespace-only string."""
        if val is None:
            return True
        if isinstance(val, str) and not val.strip():
            return True
        return False

    def _evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
        total_records = 0
        violating_rows: list[dict[str, Any]] = []

        for idx, row in enumerate(context.get_records()):
            total_records += 1
            missing_in_row = [col for col in self.columns if self._is_null_or_blank(row.get(col))]
            if missing_in_row:
                if len(violating_rows) < 20:
                    violating_rows.append(
                        {
                            "row_index": idx,
                            "missing_fields": missing_in_row,
                            "row_sample": {col: row.get(col) for col in self.columns},
                        }
                    )

        affected_count = len(violating_rows)
        # If more than 20 rows were violating, count total violating rows
        if affected_count == 20 and total_records > 20:
            total_violating = sum(
                1
                for row in context.get_records()
                if any(self._is_null_or_blank(row.get(col)) for col in self.columns)
            )
            affected_count = total_violating
        else:
            affected_count = len(violating_rows)

        if affected_count > 0:
            return self._build_result(
                status=RuleStatus.FAILED,
                affected_fields=self.columns,
                affected_record_count=affected_count,
                total_record_count=total_records,
                message=(
                    f"Found {affected_count} record(s) with missing or empty required values "
                    f"in fields: {', '.join(self.columns)}."
                ),
                evidence={
                    "sample_violations": violating_rows,
                    "columns_checked": self.columns,
                },
            )

        return self._build_result(
            status=RuleStatus.PASSED,
            affected_fields=self.columns,
            affected_record_count=0,
            total_record_count=total_records,
            message=(
                f"All {total_records} records contain valid non-null values "
                f"for fields: {', '.join(self.columns)}."
            ),
            evidence={"columns_checked": self.columns},
        )


class UniquenessRule(BaseValidationRule):
    """Rule evaluator verifying uniqueness of single primary keys or composite keys."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.columns: list[str] = []
        if "columns" in self.parameters:
            self.columns = list(self.parameters["columns"])
        elif "column" in self.parameters:
            self.columns = [str(self.parameters["column"])]
        else:
            raise ValueError("UniquenessRule requires 'column' or 'columns' parameter.")

    def _extract_key(self, row: dict[str, Any]) -> Any:
        """Extract sanitized key value or composite tuple from row."""
        if len(self.columns) == 1:
            val = row.get(self.columns[0])
            return val.strip() if isinstance(val, str) else val
        key_parts: list[Any] = []
        for col in self.columns:
            v = row.get(col)
            key_parts.append(v.strip() if isinstance(v, str) else v)
        return tuple(key_parts)

    def _evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
        key_indices: dict[Any, list[int]] = defaultdict(list)
        total_records = 0

        for idx, row in enumerate(context.get_records()):
            total_records += 1
            key = self._extract_key(row)
            key_indices[key].append(idx)

        # Identify all duplicate keys (keys with > 1 occurrence)
        duplicate_map = {k: indices for k, indices in key_indices.items() if len(indices) > 1}
        # The number of duplicate rows is the sum of excess occurrences
        affected_record_count = sum(len(indices) - 1 for indices in duplicate_map.values())

        col_label = self.columns[0] if len(self.columns) == 1 else f"({', '.join(self.columns)})"

        if affected_record_count > 0:
            sample_duplicates: list[dict[str, Any]] = []
            for k, indices in list(duplicate_map.items())[:20]:
                if len(self.columns) == 1:
                    sample_duplicates.append(
                        {
                            self.columns[0]: str(k) if k is not None else None,
                            "occurrences": len(indices),
                            "row_indices": indices,
                        }
                    )
                else:
                    composite_dict = {
                        col: (str(val) if val is not None else None)
                        for col, val in zip(self.columns, k)
                    }
                    sample_duplicates.append(
                        {
                            "composite_key": composite_dict,
                            "occurrences": len(indices),
                            "row_indices": indices,
                        }
                    )

            return self._build_result(
                status=RuleStatus.FAILED,
                affected_fields=self.columns,
                affected_record_count=affected_record_count,
                total_record_count=total_records,
                message=(
                    f"Found {affected_record_count} duplicate record(s) across "
                    f"{len(duplicate_map)} distinct key(s) in {col_label}."
                ),
                evidence={
                    "sample_duplicates": sample_duplicates,
                    "duplicate_keys_count": len(duplicate_map),
                    "columns_checked": self.columns,
                },
            )

        return self._build_result(
            status=RuleStatus.PASSED,
            affected_fields=self.columns,
            affected_record_count=0,
            total_record_count=total_records,
            message=f"All {total_records} records have unique {col_label} values.",
            evidence={"columns_checked": self.columns},
        )


class TypeValidityRule(BaseValidationRule):
    """Rule evaluator verifying data type parseability and regex pattern constraints."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if "column" not in self.parameters:
            raise ValueError("TypeValidityRule requires 'column' parameter.")
        self.column: str = str(self.parameters["column"])
        self.expected_type: str | None = self.parameters.get("expected_type")
        self.pattern: str | None = self.parameters.get("pattern")
        self.allow_null: bool = bool(self.parameters.get("allow_null", True))

        if not self.expected_type and not self.pattern:
            raise ValueError("TypeValidityRule requires at least 'expected_type' or 'pattern'.")

        self._compiled_regex: re.Pattern[str] | None = None
        if self.pattern:
            self._compiled_regex = re.compile(self.pattern)

    def _validate_value(self, val: Any) -> tuple[bool, str]:
        """Validate single value against expected type and pattern."""
        if val is None or (isinstance(val, str) and not val.strip()):
            if self.allow_null:
                return True, ""
            return False, "Value is null or blank"

        str_val = str(val).strip()

        if self.expected_type:
            t = self.expected_type.lower()
            if t == "integer":
                if isinstance(val, bool):
                    return False, "Boolean value cannot be accepted as integer"
                try:
                    # Reject decimal points in string representations of integers
                    if "." in str_val:
                        return False, f"Float string '{str_val}' cannot be parsed as integer"
                    int(str_val)
                except ValueError:
                    return False, f"Value '{str_val}' cannot be parsed as an integer"

            elif t == "float":
                if isinstance(val, bool):
                    return False, "Boolean value cannot be accepted as float"
                try:
                    float(str_val)
                except ValueError:
                    return False, f"Value '{str_val}' cannot be parsed as a float"

            elif t == "boolean":
                if not isinstance(val, bool) and str_val.lower() not in (
                    "true",
                    "false",
                    "1",
                    "0",
                    "yes",
                    "no",
                ):
                    return False, f"Value '{str_val}' cannot be parsed as boolean"

            elif t == "timestamp":
                if not isinstance(val, (datetime, date)):
                    try:
                        datetime.fromisoformat(str_val.replace("Z", "+00:00"))
                    except ValueError:
                        return False, f"Value '{str_val}' is not a valid ISO-8601 timestamp"

            elif t == "json":
                if not isinstance(val, (dict, list)):
                    try:
                        json.loads(str_val)
                    except json.JSONDecodeError:
                        return False, f"Value '{str_val}' is not valid JSON"

        if self._compiled_regex is not None:
            if not self._compiled_regex.fullmatch(str_val):
                return False, f"Value '{str_val}' does not match pattern '{self.pattern}'"

        return True, ""

    def _evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
        total_records = 0
        violations: list[dict[str, Any]] = []
        total_violating_count = 0

        for idx, row in enumerate(context.get_records()):
            total_records += 1
            is_valid, reason = self._validate_value(row.get(self.column))
            if not is_valid:
                total_violating_count += 1
                if len(violations) < 20:
                    violations.append(
                        {
                            "row_index": idx,
                            "column": self.column,
                            "observed_value": str(row.get(self.column)),
                            "reason": reason,
                        }
                    )

        if total_violating_count > 0:
            return self._build_result(
                status=RuleStatus.FAILED,
                affected_fields=[self.column],
                affected_record_count=total_violating_count,
                total_record_count=total_records,
                message=(
                    f"Found {total_violating_count} record(s) with invalid format or type "
                    f"in column '{self.column}'."
                ),
                evidence={
                    "sample_violations": violations,
                    "expected_type": self.expected_type,
                    "pattern": self.pattern,
                },
            )

        return self._build_result(
            status=RuleStatus.PASSED,
            affected_fields=[self.column],
            affected_record_count=0,
            total_record_count=total_records,
            message=(
                f"All {total_records} records in '{self.column}' "
                "satisfy type and format requirements."
            ),
            evidence={
                "expected_type": self.expected_type,
                "pattern": self.pattern,
            },
        )


class RecordCountRule(BaseValidationRule):
    """Rule evaluator verifying total record count bounds (min, max, exact)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.min_count: int | None = self.parameters.get("min_count")
        self.max_count: int | None = self.parameters.get("max_count")
        self.exact_count: int | None = self.parameters.get("exact_count")

        if self.min_count is None and self.max_count is None and self.exact_count is None:
            raise ValueError(
                "RecordCountRule requires at least one of "
                "'min_count', 'max_count', or 'exact_count'."
            )

    def _evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
        total_records = context.get_record_count()
        violation = False
        message = ""
        diff = 0

        if self.exact_count is not None and total_records != self.exact_count:
            violation = True
            diff = abs(total_records - self.exact_count)
            message = (
                f"Dataset record count {total_records} does not match "
                f"expected exact count of {self.exact_count}."
            )
        elif self.min_count is not None and total_records < self.min_count:
            violation = True
            diff = self.min_count - total_records
            message = (
                f"Dataset record count {total_records} is below "
                f"required minimum of {self.min_count}."
            )
        elif self.max_count is not None and total_records > self.max_count:
            violation = True
            diff = total_records - self.max_count
            message = (
                f"Dataset record count {total_records} exceeds "
                f"permitted maximum of {self.max_count}."
            )

        evidence = {
            "observed_count": total_records,
            "min_count": self.min_count,
            "max_count": self.max_count,
            "exact_count": self.exact_count,
        }

        if violation:
            return self._build_result(
                status=RuleStatus.FAILED,
                affected_fields=[],
                affected_record_count=diff,
                total_record_count=total_records,
                message=message,
                evidence=evidence,
            )

        return self._build_result(
            status=RuleStatus.PASSED,
            affected_fields=[],
            affected_record_count=0,
            total_record_count=total_records,
            message=f"Dataset record count {total_records} satisfies count threshold constraints.",
            evidence=evidence,
        )


class ValueRangeRule(BaseValidationRule):
    """Rule evaluator asserting numeric lower and upper bounds."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if "column" not in self.parameters:
            raise ValueError("ValueRangeRule requires 'column' parameter.")
        self.column: str = str(self.parameters["column"])
        self.min_value: float | None = (
            float(self.parameters["min_value"]) if "min_value" in self.parameters else None
        )
        self.max_value: float | None = (
            float(self.parameters["max_value"]) if "max_value" in self.parameters else None
        )
        self.inclusive_min: bool = bool(self.parameters.get("inclusive_min", True))
        self.inclusive_max: bool = bool(self.parameters.get("inclusive_max", True))
        self.allow_null: bool = bool(self.parameters.get("allow_null", True))

        if self.min_value is None and self.max_value is None:
            raise ValueError("ValueRangeRule requires at least 'min_value' or 'max_value'.")

    def _evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
        total_records = 0
        violations: list[dict[str, Any]] = []
        total_violating_count = 0

        for idx, row in enumerate(context.get_records()):
            total_records += 1
            raw_val = row.get(self.column)

            if raw_val is None or (isinstance(raw_val, str) and not raw_val.strip()):
                if self.allow_null:
                    continue
                total_violating_count += 1
                if len(violations) < 20:
                    violations.append(
                        {
                            "row_index": idx,
                            "column": self.column,
                            "observed_value": raw_val,
                            "reason": "Value is null or blank",
                        }
                    )
                continue

            try:
                num_val = float(raw_val)
            except (ValueError, TypeError):
                total_violating_count += 1
                if len(violations) < 20:
                    violations.append(
                        {
                            "row_index": idx,
                            "column": self.column,
                            "observed_value": raw_val,
                            "reason": f"Value '{raw_val}' cannot be converted to numeric float",
                        }
                    )
                continue

            # Min value check
            if self.min_value is not None:
                if self.inclusive_min and num_val < self.min_value:
                    total_violating_count += 1
                    if len(violations) < 20:
                        violations.append(
                            {
                                "row_index": idx,
                                "column": self.column,
                                "observed_value": num_val,
                                "reason": f"Value {num_val} is less than minimum {self.min_value}",
                            }
                        )
                    continue
                elif not self.inclusive_min and num_val <= self.min_value:
                    total_violating_count += 1
                    if len(violations) < 20:
                        violations.append(
                            {
                                "row_index": idx,
                                "column": self.column,
                                "observed_value": num_val,
                                "reason": (
                                    f"Value {num_val} is not strictly greater than {self.min_value}"
                                ),
                            }
                        )
                    continue

            # Max value check
            if self.max_value is not None:
                if self.inclusive_max and num_val > self.max_value:
                    total_violating_count += 1
                    if len(violations) < 20:
                        violations.append(
                            {
                                "row_index": idx,
                                "column": self.column,
                                "observed_value": num_val,
                                "reason": f"Value {num_val} exceeds maximum {self.max_value}",
                            }
                        )
                    continue
                elif not self.inclusive_max and num_val >= self.max_value:
                    total_violating_count += 1
                    if len(violations) < 20:
                        violations.append(
                            {
                                "row_index": idx,
                                "column": self.column,
                                "observed_value": num_val,
                                "reason": (
                                    f"Value {num_val} is not strictly less than {self.max_value}"
                                ),
                            }
                        )
                    continue

        evidence = {
            "sample_violations": violations,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "inclusive_min": self.inclusive_min,
            "inclusive_max": self.inclusive_max,
        }

        if total_violating_count > 0:
            return self._build_result(
                status=RuleStatus.FAILED,
                affected_fields=[self.column],
                affected_record_count=total_violating_count,
                total_record_count=total_records,
                message=(
                    f"Found {total_violating_count} record(s) violating value range constraints "
                    f"on column '{self.column}'."
                ),
                evidence=evidence,
            )

        return self._build_result(
            status=RuleStatus.PASSED,
            affected_fields=[self.column],
            affected_record_count=0,
            total_record_count=total_records,
            message=f"All {total_records} records in '{self.column}' fall within expected range.",
            evidence=evidence,
        )
