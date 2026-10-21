"""Base validation rule abstraction and validation execution context."""

from __future__ import annotations

import csv
import json
import time
from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.schemas.validation import (
    RuleCategory,
    RuleEvaluationResult,
    RuleSeverity,
    RuleStatus,
)


class ValidationContext:
    """Execution context provided to rule evaluators containing dataset records and metadata."""

    def __init__(
        self,
        dataset_id: str,
        records: list[dict[str, Any]] | None = None,
        file_path: Path | None = None,
        file_format: str = "csv",
        scenario_id: str | None = None,
        total_record_count: int | None = None,
        datasets: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.dataset_id = dataset_id
        self._records = records
        self.file_path = file_path
        self.file_format = file_format.lower()
        self.scenario_id = scenario_id
        self._total_record_count = total_record_count
        self.datasets = datasets or {}

    def get_records(self) -> Iterable[dict[str, Any]]:
        """Yield records either from in-memory list or streamed from file."""
        if self._records is not None:
            yield from self._records
            return

        if self.file_path is None or not self.file_path.exists():
            return

        if self.file_format == "csv":
            with open(self.file_path, encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield dict(row)
        elif self.file_format == "json":
            with open(self.file_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                yield from data
            elif isinstance(data, dict):
                items = data.get("records") or data.get("data") or [data]
                if isinstance(items, list):
                    yield from items

    def get_records_as_list(self) -> list[dict[str, Any]]:
        """Retrieve all records as a materialized list, caching if necessary."""
        if self._records is not None:
            return self._records
        self._records = list(self.get_records())
        self._total_record_count = len(self._records)
        return self._records

    def get_record_count(self) -> int:
        """Return total record count for the primary dataset."""
        if self._total_record_count is not None:
            return self._total_record_count
        if self._records is not None:
            self._total_record_count = len(self._records)
            return self._total_record_count
        # Materialize or count from stream
        records = self.get_records_as_list()
        return len(records)


class BaseValidationRule(ABC):
    """Abstract base class for all deterministic data quality rules."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        dataset_id: str,
        category: RuleCategory | str,
        severity: RuleSeverity | str = RuleSeverity.HIGH,
        parameters: dict[str, Any] | None = None,
        description: str = "",
        is_active: bool = True,
    ) -> None:
        self.rule_id = rule_id
        self.name = name
        self.dataset_id = dataset_id
        if isinstance(category, RuleCategory):
            self.category: RuleCategory | str = category
        else:
            try:
                self.category = RuleCategory(str(category))
            except ValueError:
                self.category = str(category)

        if isinstance(severity, RuleSeverity):
            self.severity: RuleSeverity | str = severity
        else:
            try:
                self.severity = RuleSeverity(str(severity))
            except ValueError:
                self.severity = str(severity)
        self.parameters = parameters or {}
        self.description = description
        self.is_active = is_active

    def evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
        """Template method that evaluates the rule, catches errors, and measures timing."""
        if not self.is_active:
            return self._build_result(
                status=RuleStatus.SKIPPED,
                affected_fields=[],
                affected_record_count=0,
                total_record_count=context.get_record_count(),
                message=f"Rule '{self.name}' ({self.rule_id}) is inactive and was skipped.",
                evidence={"reason": "Rule is marked inactive"},
                duration_ms=0,
            )

        start_time = time.perf_counter()
        try:
            result = self._evaluate(context)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return self._build_result(
                status=RuleStatus.ERROR,
                affected_fields=[],
                affected_record_count=0,
                total_record_count=context.get_record_count(),
                message=f"Rule evaluation encountered an unexpected error: {exc}",
                evidence={"error": str(exc), "error_type": exc.__class__.__name__},
                duration_ms=duration_ms,
            )

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        # If evaluator recorded 0 ms due to high resolution sub-millisecond execution, keep measured
        if result.execution_duration_ms == 0:
            result.execution_duration_ms = duration_ms
        return result

    @abstractmethod
    def _evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
        """Execute concrete evaluation logic and return findings."""
        pass

    def _build_result(
        self,
        status: RuleStatus | str,
        affected_fields: list[str],
        affected_record_count: int,
        total_record_count: int,
        message: str,
        evidence: dict[str, Any] | None = None,
        duration_ms: int = 0,
    ) -> RuleEvaluationResult:
        """Helper to construct a validated RuleEvaluationResult."""
        status_val: RuleStatus | str
        if isinstance(status, RuleStatus):
            status_val = status
        else:
            try:
                status_val = RuleStatus(str(status))
            except ValueError:
                status_val = str(status)

        return RuleEvaluationResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            rule_category=self.category,
            severity=self.severity,
            status=status_val,
            dataset_id=self.dataset_id,
            affected_fields=affected_fields,
            affected_record_count=affected_record_count,
            total_record_count=total_record_count,
            message=message,
            evidence=evidence or {},
            execution_duration_ms=duration_ms,
        )

