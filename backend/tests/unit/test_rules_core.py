"""Unit tests for the validation rule framework and core rule evaluators.

Acceptance Criteria:
1. UniquenessRule accurately detects 15 duplicates in orders.csv sample with line indices and keys.
2. ValueRangeRule accurately detects 8 negative inventory SKUs in inventory.csv.
3. Unit test suite passes with >90% code coverage.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.config import settings
from app.core.errors import LuxException
from app.schemas.validation import (
    RuleCategory,
    RuleEvaluationResult,
    RuleSeverity,
    RuleStatus,
    ValidationRuleConfig,
)
from app.services.validation.base import BaseValidationRule, ValidationContext
from app.services.validation.core import (
    NullCheckRule,
    RecordCountRule,
    TypeValidityRule,
    UniquenessRule,
    ValueRangeRule,
)
from app.services.validation.registry import RuleRegistry


@pytest.fixture
def defective_scenario_dir() -> Path:
    """Fixture providing path to defective scenario fixtures."""
    path = settings.scenarios_dir / "monday_revenue_mystery" / "defective"
    assert path.is_dir()
    return path


@pytest.fixture
def corrected_scenario_dir() -> Path:
    """Fixture providing path to corrected scenario fixtures."""
    path = settings.scenarios_dir / "monday_revenue_mystery" / "corrected"
    assert path.is_dir()
    return path


# ---------------------------------------------------------------------------
# 1. ValidationContext Tests
# ---------------------------------------------------------------------------


def test_validation_context_in_memory() -> None:
    """Test ValidationContext with in-memory records."""
    data = [{"id": "1", "name": "Alpha"}, {"id": "2", "name": "Beta"}]
    ctx = ValidationContext(dataset_id="test_ds", records=data)

    assert ctx.dataset_id == "test_ds"
    assert ctx.get_record_count() == 2
    assert list(ctx.get_records()) == data
    assert ctx.get_records_as_list() == data


def test_validation_context_csv_streaming(tmp_path: Path) -> None:
    """Test ValidationContext streaming from a CSV file."""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("id,val\n10,A\n20,B\n30,C\n", encoding="utf-8")

    ctx = ValidationContext(dataset_id="csv_ds", file_path=csv_file, file_format="csv")
    assert ctx.get_record_count() == 3
    records = list(ctx.get_records())
    assert len(records) == 3
    assert records[0] == {"id": "10", "val": "A"}
    assert records[2] == {"id": "30", "val": "C"}


def test_validation_context_json_streaming(tmp_path: Path) -> None:
    """Test ValidationContext streaming from a JSON file."""
    json_file = tmp_path / "sample.json"
    json_file.write_text(
        json.dumps([{"sku": "SKU-1", "qty": 5}, {"sku": "SKU-2", "qty": 10}]),
        encoding="utf-8",
    )

    ctx = ValidationContext(dataset_id="json_ds", file_path=json_file, file_format="json")
    assert ctx.get_record_count() == 2
    records = list(ctx.get_records())
    assert records[0]["sku"] == "SKU-1"


def test_validation_context_json_object_wrapper(tmp_path: Path) -> None:
    """Test ValidationContext with JSON wrapped in records/data key."""
    json_file = tmp_path / "wrapped.json"
    json_file.write_text(
        json.dumps({"records": [{"id": 100}, {"id": 200}]}),
        encoding="utf-8",
    )

    ctx = ValidationContext(dataset_id="json_ds", file_path=json_file, file_format="json")
    records = list(ctx.get_records())
    assert len(records) == 2
    assert records[1]["id"] == 200


def test_validation_context_missing_file(tmp_path: Path) -> None:
    """Test ValidationContext handles non-existent file path gracefully."""
    ctx = ValidationContext(dataset_id="empty_ds", file_path=tmp_path / "non_existent.csv")
    assert list(ctx.get_records()) == []
    assert ctx.get_record_count() == 0


# ---------------------------------------------------------------------------
# 2. BaseValidationRule Tests
# ---------------------------------------------------------------------------


class DummyCrashingRule(BaseValidationRule):
    """Rule that raises an unexpected exception for error testing."""

    def _evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
        raise RuntimeError("Simulated crash in evaluator")


def test_base_rule_inactive_skipped() -> None:
    """Test that inactive rules return SKIPPED status."""
    rule = NullCheckRule(
        rule_id="RULE-INACTIVE",
        name="Inactive Check",
        dataset_id="orders",
        category=RuleCategory.NULL_CHECK,
        parameters={"column": "order_id"},
        is_active=False,
    )
    ctx = ValidationContext(dataset_id="orders", records=[{"order_id": None}])
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.SKIPPED
    assert res.affected_record_count == 0
    assert "inactive" in res.message.lower()


def test_base_rule_exception_handling() -> None:
    """Test that unexpected evaluator exceptions are caught and reported as ERROR status."""
    rule = DummyCrashingRule(
        rule_id="RULE-CRASH",
        name="Crashing Rule",
        dataset_id="orders",
        category=RuleCategory.NULL_CHECK,
    )
    ctx = ValidationContext(dataset_id="orders", records=[{"a": 1}])
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.ERROR
    assert "Simulated crash" in res.message
    assert res.evidence["error_type"] == "RuntimeError"


# ---------------------------------------------------------------------------
# 3. RuleRegistry Tests
# ---------------------------------------------------------------------------


def test_rule_registry_instantiation() -> None:
    """Test dynamic instantiation from dict and Pydantic config."""
    config_dict = {
        "id": "VAL-NULL-001",
        "dataset_id": "customers",
        "name": "Customer Name Check",
        "category": "NULL_CHECK",
        "severity": "CRITICAL",
        "parameters": {"column": "email"},
        "description": "Email must not be null",
    }
    rule = RuleRegistry.create_rule(config_dict)
    assert isinstance(rule, NullCheckRule)
    assert rule.rule_id == "VAL-NULL-001"
    assert rule.columns == ["email"]

    pydantic_config = ValidationRuleConfig(
        id="VAL-UNIQ-001",
        dataset_id="customers",
        name="Customer ID Uniqueness",
        category=RuleCategory.UNIQUENESS,
        severity=RuleSeverity.HIGH,
        parameters={"column": "customer_id"},
    )
    rule2 = RuleRegistry.create_rule(pydantic_config)
    assert isinstance(rule2, UniquenessRule)
    assert rule2.rule_id == "VAL-UNIQ-001"


def test_rule_registry_parameters_json_string() -> None:
    """Test dynamic instantiation when parameters is a JSON string (as from SQLite)."""
    config_dict = {
        "id": "VAL-RANGE-001",
        "dataset_id": "inventory",
        "name": "Inventory Check",
        "category": "VALUE_RANGE",
        "parameters": '{"column": "quantity", "min_value": 0}',
    }
    rule = RuleRegistry.create_rule(config_dict)
    assert isinstance(rule, ValueRangeRule)
    assert rule.min_value == 0.0


def test_rule_registry_unknown_category() -> None:
    """Test that creating a rule with an unknown category raises LuxException."""
    with pytest.raises(LuxException) as exc_info:
        RuleRegistry.create_rule(
            {
                "id": "VAL-UNKNOWN",
                "category": "NON_EXISTENT_CATEGORY",
            }
        )
    assert exc_info.value.code == "UNKNOWN_RULE_CATEGORY"


def test_rule_registry_custom_registration() -> None:
    """Test registering a custom rule class."""

    @RuleRegistry.register_rule("CUSTOM_TEST_RULE")
    class CustomRule(BaseValidationRule):
        def _evaluate(self, context: ValidationContext) -> RuleEvaluationResult:
            return self._build_result(
                status=RuleStatus.PASSED,
                affected_fields=[],
                affected_record_count=0,
                total_record_count=0,
                message="Custom rule passed",
            )

    assert RuleRegistry.is_registered("CUSTOM_TEST_RULE")
    created = RuleRegistry.create_rule(
        {
            "id": "CUST-001",
            "category": "CUSTOM_TEST_RULE",
        }
    )
    assert isinstance(created, CustomRule)


# ---------------------------------------------------------------------------
# 4. NullCheckRule Tests
# ---------------------------------------------------------------------------


def test_null_check_missing_column_param() -> None:
    """Verify NullCheckRule raises ValueError if column parameter missing."""
    with pytest.raises(ValueError, match="NullCheckRule requires"):
        NullCheckRule(
            rule_id="NULL-ERR",
            name="Err",
            dataset_id="ds",
            category=RuleCategory.NULL_CHECK,
            parameters={},
        )


def test_null_check_clean_records() -> None:
    """Verify NullCheckRule passes when all required fields have values."""
    records = [
        {"id": "1", "name": "Alice", "email": "alice@example.com"},
        {"id": "2", "name": "Bob", "email": "bob@example.com"},
    ]
    ctx = ValidationContext(dataset_id="users", records=records)
    rule = NullCheckRule(
        rule_id="NULL-01",
        name="Mandatory User Fields",
        dataset_id="users",
        category=RuleCategory.NULL_CHECK,
        parameters={"columns": ["id", "name", "email"]},
    )
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.PASSED
    assert res.affected_record_count == 0
    assert res.total_record_count == 2
    assert "valid non-null" in res.message


def test_null_check_whitespace_and_empty_cells() -> None:
    """Verify NullCheckRule detects None, empty string, and whitespace-only cells."""
    records = [
        {"id": "1", "name": "Alice"},  # clean
        {"id": "2", "name": None},  # explicit None
        {"id": "3", "name": ""},  # empty string
        {"id": "4", "name": "   "},  # whitespace-only cell (edge case)
        {"id": "5", "name": "\t \n "},  # whitespace tabs/newlines
    ]
    ctx = ValidationContext(dataset_id="users", records=records)
    rule = NullCheckRule(
        rule_id="NULL-02",
        name="Name Mandatory",
        dataset_id="users",
        category=RuleCategory.NULL_CHECK,
        parameters={"column": "name"},
    )
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.FAILED
    assert res.affected_record_count == 4
    assert res.total_record_count == 5
    assert len(res.evidence["sample_violations"]) == 4
    violating_indices = [v["row_index"] for v in res.evidence["sample_violations"]]
    assert violating_indices == [1, 2, 3, 4]


# ---------------------------------------------------------------------------
# 5. UniquenessRule Tests & Acceptance Criteria
# ---------------------------------------------------------------------------


def test_uniqueness_missing_column_param() -> None:
    """Verify UniquenessRule raises ValueError if column parameter missing."""
    with pytest.raises(ValueError, match="UniquenessRule requires"):
        UniquenessRule(
            rule_id="U-ERR",
            name="Err",
            dataset_id="ds",
            category=RuleCategory.UNIQUENESS,
            parameters={},
        )


def test_uniqueness_clean_records() -> None:
    """Verify UniquenessRule passes on distinct records."""
    records = [{"sku": "A1"}, {"sku": "A2"}, {"sku": "A3"}]
    ctx = ValidationContext(dataset_id="items", records=records)
    rule = UniquenessRule(
        rule_id="U-01",
        name="SKU Uniqueness",
        dataset_id="items",
        category=RuleCategory.UNIQUENESS,
        parameters={"column": "sku"},
    )
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.PASSED
    assert res.affected_record_count == 0
    assert res.total_record_count == 3


def test_uniqueness_composite_keys() -> None:
    """Verify UniquenessRule properly evaluates composite multi-column keys."""
    records = [
        {"warehouse": "WH1", "sku": "SKU-A"},
        {"warehouse": "WH2", "sku": "SKU-A"},  # same sku, diff warehouse -> unique
        {"warehouse": "WH1", "sku": "SKU-B"},
        {"warehouse": "WH1", "sku": "SKU-A"},  # duplicate of row 0
    ]
    ctx = ValidationContext(dataset_id="inv", records=records)
    rule = UniquenessRule(
        rule_id="U-02",
        name="Composite Uniqueness",
        dataset_id="inv",
        category=RuleCategory.UNIQUENESS,
        parameters={"columns": ["warehouse", "sku"]},
    )
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.FAILED
    assert res.affected_record_count == 1
    assert len(res.evidence["sample_duplicates"]) == 1
    sample = res.evidence["sample_duplicates"][0]
    assert sample["composite_key"] == {"warehouse": "WH1", "sku": "SKU-A"}
    assert sample["occurrences"] == 2
    assert sample["row_indices"] == [0, 3]


def test_uniqueness_acceptance_criteria_orders_defective(
    defective_scenario_dir: Path,
) -> None:
    """ACCEPTANCE CRITERIA: UniquenessRule accurately detects 15 duplicates in orders.csv

    sample with line indices and keys.
    """
    orders_csv = defective_scenario_dir / "orders.csv"
    assert orders_csv.is_file()

    ctx = ValidationContext(dataset_id="orders", file_path=orders_csv, file_format="csv")
    rule = UniquenessRule(
        rule_id="VAL-ORD-001",
        name="Order ID Uniqueness Check",
        dataset_id="orders",
        category=RuleCategory.UNIQUENESS,
        severity=RuleSeverity.CRITICAL,
        parameters={"column": "order_id"},
    )
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.FAILED
    assert res.total_record_count == 1250
    assert res.affected_record_count == 15
    assert res.affected_fields == ["order_id"]
    assert res.evidence["duplicate_keys_count"] == 15

    # Check that sample duplicates contains keys and row indices
    sample_dups = res.evidence["sample_duplicates"]
    assert len(sample_dups) == 15
    for item in sample_dups:
        assert "order_id" in item
        assert item["occurrences"] == 2
        assert len(item["row_indices"]) == 2
        # Verify indices are distinct
        assert item["row_indices"][0] != item["row_indices"][1]

    # Verify specific known duplicates from fixture generation
    dup_keys = {item["order_id"] for item in sample_dups}
    assert "ORD-0015" in dup_keys
    ord_15_item = next(i for i in sample_dups if i["order_id"] == "ORD-0015")
    assert ord_15_item["row_indices"] == [14, 1235]


def test_uniqueness_acceptance_criteria_orders_corrected(
    corrected_scenario_dir: Path,
) -> None:
    """Verify UniquenessRule passes on corrected orders.csv with 0 duplicates."""
    orders_csv = corrected_scenario_dir / "orders.csv"
    assert orders_csv.is_file()

    ctx = ValidationContext(dataset_id="orders", file_path=orders_csv, file_format="csv")
    rule = UniquenessRule(
        rule_id="VAL-ORD-001",
        name="Order ID Uniqueness Check",
        dataset_id="orders",
        category=RuleCategory.UNIQUENESS,
        parameters={"column": "order_id"},
    )
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.PASSED
    assert res.total_record_count == 1250
    assert res.affected_record_count == 0


# ---------------------------------------------------------------------------
# 6. TypeValidityRule Tests
# ---------------------------------------------------------------------------


def test_type_validity_param_validation() -> None:
    """Verify TypeValidityRule requires column and at least expected_type or pattern."""
    with pytest.raises(ValueError, match="TypeValidityRule requires 'column'"):
        TypeValidityRule(
            rule_id="T-ERR1",
            name="Err",
            dataset_id="ds",
            category=RuleCategory.TYPE_VALIDITY,
            parameters={},
        )

    with pytest.raises(ValueError, match="requires at least 'expected_type' or 'pattern'"):
        TypeValidityRule(
            rule_id="T-ERR2",
            name="Err",
            dataset_id="ds",
            category=RuleCategory.TYPE_VALIDITY,
            parameters={"column": "val"},
        )


def test_type_validity_integer() -> None:
    """Verify TypeValidityRule detects integer parseability and rejects non-integers."""
    records = [
        {"qty": 10},
        {"qty": "42"},
        {"qty": "-5"},
        {"qty": "3.14"},  # float string -> invalid integer
        {"qty": "abc"},  # non-numeric -> invalid integer
        {"qty": True},  # boolean -> invalid integer
    ]
    ctx = ValidationContext(dataset_id="t", records=records)
    rule = TypeValidityRule(
        rule_id="T-INT",
        name="Qty Integer Check",
        dataset_id="t",
        category=RuleCategory.TYPE_VALIDITY,
        parameters={"column": "qty", "expected_type": "integer"},
    )
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.FAILED
    assert res.affected_record_count == 3
    assert len(res.evidence["sample_violations"]) == 3


def test_type_validity_float() -> None:
    """Verify TypeValidityRule validates floats."""
    records = [
        {"amount": 10.5},
        {"amount": "42.99"},
        {"amount": 100},
        {"amount": "invalid_number"},
    ]
    ctx = ValidationContext(dataset_id="t", records=records)
    rule = TypeValidityRule(
        rule_id="T-FLOAT",
        name="Amount Float Check",
        dataset_id="t",
        category=RuleCategory.TYPE_VALIDITY,
        parameters={"column": "amount", "expected_type": "float"},
    )
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.FAILED
    assert res.affected_record_count == 1
    assert res.evidence["sample_violations"][0]["row_index"] == 3


def test_type_validity_boolean_and_timestamp() -> None:
    """Verify TypeValidityRule validates booleans and ISO timestamps."""
    # Booleans
    b_records = [{"flag": "true"}, {"flag": "FALSE"}, {"flag": "0"}, {"flag": "maybe"}]
    b_ctx = ValidationContext(dataset_id="t", records=b_records)
    b_rule = TypeValidityRule(
        rule_id="T-BOOL",
        name="Bool Check",
        dataset_id="t",
        category=RuleCategory.TYPE_VALIDITY,
        parameters={"column": "flag", "expected_type": "boolean"},
    )
    assert b_rule.evaluate(b_ctx).affected_record_count == 1

    # Timestamps
    ts_records = [
        {"ts": "2026-10-19T08:14:22Z"},
        {"ts": "2026-10-19 12:00:00"},
        {"ts": "invalid-date-format"},
    ]
    ts_ctx = ValidationContext(dataset_id="t", records=ts_records)
    ts_rule = TypeValidityRule(
        rule_id="T-TS",
        name="Timestamp Check",
        dataset_id="t",
        category=RuleCategory.TYPE_VALIDITY,
        parameters={"column": "ts", "expected_type": "timestamp"},
    )
    assert ts_rule.evaluate(ts_ctx).affected_record_count == 1


def test_type_validity_json() -> None:
    """Verify TypeValidityRule validates JSON strings and structures."""
    records = [
        {"meta": '{"key": "value"}'},
        {"meta": {"already": "dict"}},
        {"meta": "{broken json}"},
    ]
    ctx = ValidationContext(dataset_id="t", records=records)
    rule = TypeValidityRule(
        rule_id="T-JSON",
        name="JSON Check",
        dataset_id="t",
        category=RuleCategory.TYPE_VALIDITY,
        parameters={"column": "meta", "expected_type": "json"},
    )
    res = rule.evaluate(ctx)
    assert res.affected_record_count == 1
    assert res.evidence["sample_violations"][0]["row_index"] == 2


def test_type_validity_regex_pattern() -> None:
    """Verify TypeValidityRule validates custom regex pattern."""
    records = [
        {"order_id": "ORD-1001"},
        {"order_id": "ORD-9999"},
        {"order_id": "ORDER_1001"},  # invalid format
        {"order_id": "ORD-ABC"},  # letters instead of digits
    ]
    ctx = ValidationContext(dataset_id="t", records=records)
    rule = TypeValidityRule(
        rule_id="T-REGEX",
        name="Order ID Format Check",
        dataset_id="t",
        category=RuleCategory.TYPE_VALIDITY,
        parameters={"column": "order_id", "pattern": r"^ORD-\d{4}$"},
    )
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.FAILED
    assert res.affected_record_count == 2
    assert res.evidence["sample_violations"][0]["observed_value"] == "ORDER_1001"
    assert res.evidence["sample_violations"][1]["observed_value"] == "ORD-ABC"


def test_type_validity_allow_null() -> None:
    """Verify TypeValidityRule respects allow_null flag."""
    records = [{"val": "123"}, {"val": None}, {"val": "  "}]
    ctx = ValidationContext(dataset_id="t", records=records)

    # With allow_null=True (default)
    rule_allowed = TypeValidityRule(
        rule_id="T-NULL-1",
        name="Allow Null",
        dataset_id="t",
        category=RuleCategory.TYPE_VALIDITY,
        parameters={"column": "val", "expected_type": "integer", "allow_null": True},
    )
    assert rule_allowed.evaluate(ctx).status == RuleStatus.PASSED

    # With allow_null=False
    rule_strict = TypeValidityRule(
        rule_id="T-NULL-2",
        name="Strict No Null",
        dataset_id="t",
        category=RuleCategory.TYPE_VALIDITY,
        parameters={"column": "val", "expected_type": "integer", "allow_null": False},
    )
    res_strict = rule_strict.evaluate(ctx)
    assert res_strict.status == RuleStatus.FAILED
    assert res_strict.affected_record_count == 2


# ---------------------------------------------------------------------------
# 7. RecordCountRule Tests
# ---------------------------------------------------------------------------


def test_record_count_param_validation() -> None:
    """Verify RecordCountRule requires at least one threshold parameter."""
    with pytest.raises(ValueError, match="RecordCountRule requires at least one"):
        RecordCountRule(
            rule_id="CNT-ERR",
            name="Err",
            dataset_id="ds",
            category=RuleCategory.RECORD_COUNT,
            parameters={},
        )


def test_record_count_exact_match() -> None:
    """Verify RecordCountRule exact match evaluation."""
    ctx = ValidationContext(dataset_id="ds", total_record_count=1250)
    rule_pass = RecordCountRule(
        rule_id="CNT-01",
        name="Exact Check",
        dataset_id="ds",
        category=RuleCategory.RECORD_COUNT,
        parameters={"exact_count": 1250},
    )
    assert rule_pass.evaluate(ctx).status == RuleStatus.PASSED

    rule_fail = RecordCountRule(
        rule_id="CNT-02",
        name="Exact Check Fail",
        dataset_id="ds",
        category=RuleCategory.RECORD_COUNT,
        parameters={"exact_count": 1200},
    )
    res = rule_fail.evaluate(ctx)
    assert res.status == RuleStatus.FAILED
    assert res.affected_record_count == 50


def test_record_count_min_and_max_bounds() -> None:
    """Verify RecordCountRule min and max threshold boundaries."""
    ctx = ValidationContext(dataset_id="ds", total_record_count=50)

    # Min bound satisfied
    rule_min_pass = RecordCountRule(
        rule_id="CNT-MIN-P",
        name="Min Pass",
        dataset_id="ds",
        category=RuleCategory.RECORD_COUNT,
        parameters={"min_count": 10, "max_count": 100},
    )
    assert rule_min_pass.evaluate(ctx).status == RuleStatus.PASSED

    # Below min
    rule_min_fail = RecordCountRule(
        rule_id="CNT-MIN-F",
        name="Min Fail",
        dataset_id="ds",
        category=RuleCategory.RECORD_COUNT,
        parameters={"min_count": 100},
    )
    assert rule_min_fail.evaluate(ctx).status == RuleStatus.FAILED

    # Exceeds max
    rule_max_fail = RecordCountRule(
        rule_id="CNT-MAX-F",
        name="Max Fail",
        dataset_id="ds",
        category=RuleCategory.RECORD_COUNT,
        parameters={"max_count": 30},
    )
    assert rule_max_fail.evaluate(ctx).status == RuleStatus.FAILED


# ---------------------------------------------------------------------------
# 8. ValueRangeRule Tests & Acceptance Criteria
# ---------------------------------------------------------------------------


def test_value_range_param_validation() -> None:
    """Verify ValueRangeRule parameter validations."""
    with pytest.raises(ValueError, match="ValueRangeRule requires 'column'"):
        ValueRangeRule(
            rule_id="R-ERR1",
            name="Err",
            dataset_id="ds",
            category=RuleCategory.VALUE_RANGE,
            parameters={"min_value": 0},
        )

    with pytest.raises(ValueError, match="requires at least 'min_value' or 'max_value'"):
        ValueRangeRule(
            rule_id="R-ERR2",
            name="Err",
            dataset_id="ds",
            category=RuleCategory.VALUE_RANGE,
            parameters={"column": "price"},
        )


def test_value_range_numeric_boundaries() -> None:
    """Verify ValueRangeRule handles inclusive and exclusive limits."""
    records = [
        {"price": 10.0},
        {"price": 0.0},
        {"price": -5.0},
        {"price": 105.0},
        {"price": "not_a_number"},
    ]
    ctx = ValidationContext(dataset_id="prices", records=records)

    # Inclusive min=0, max=100
    rule = ValueRangeRule(
        rule_id="R-BOUND",
        name="Price Range",
        dataset_id="prices",
        category=RuleCategory.VALUE_RANGE,
        parameters={"column": "price", "min_value": 0, "max_value": 100},
    )
    res = rule.evaluate(ctx)
    assert res.status == RuleStatus.FAILED
    # Violations: -5.0 (< 0), 105.0 (> 100), 'not_a_number'
    assert res.affected_record_count == 3


def test_value_range_exclusive_boundaries() -> None:
    """Verify ValueRangeRule with inclusive_min=False and inclusive_max=False."""
    records = [
        {"val": 0.0},  # equal to min 0.0 -> fails if exclusive
        {"val": 5.0},  # strictly between
        {"val": 10.0},  # equal to max 10.0 -> fails if exclusive
    ]
    ctx = ValidationContext(dataset_id="vals", records=records)
    rule = ValueRangeRule(
        rule_id="R-EXCL",
        name="Exclusive Range",
        dataset_id="vals",
        category=RuleCategory.VALUE_RANGE,
        parameters={
            "column": "val",
            "min_value": 0.0,
            "max_value": 10.0,
            "inclusive_min": False,
            "inclusive_max": False,
        },
    )
    res = rule.evaluate(ctx)
    assert res.status == RuleStatus.FAILED
    assert res.affected_record_count == 2


def test_value_range_acceptance_criteria_inventory_defective(
    defective_scenario_dir: Path,
) -> None:
    """ACCEPTANCE CRITERIA: ValueRangeRule accurately detects 8 negative inventory SKUs

    in inventory.csv.
    """
    inventory_csv = defective_scenario_dir / "inventory.csv"
    assert inventory_csv.is_file()

    ctx = ValidationContext(dataset_id="inventory", file_path=inventory_csv, file_format="csv")
    rule = ValueRangeRule(
        rule_id="VAL-INV-001",
        name="Inventory Non-Negative Check",
        dataset_id="inventory",
        category=RuleCategory.VALUE_RANGE,
        severity=RuleSeverity.HIGH,
        parameters={"column": "quantity_on_hand", "min_value": 0},
    )
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.FAILED
    assert res.total_record_count == 250
    assert res.affected_record_count == 8
    assert res.affected_fields == ["quantity_on_hand"]
    assert len(res.evidence["sample_violations"]) == 8

    # Verify all reported violations have negative values
    for v in res.evidence["sample_violations"]:
        assert v["column"] == "quantity_on_hand"
        assert v["observed_value"] < 0
        assert "less than minimum 0.0" in v["reason"]

    # Verify first defective item matches fixture generation (SKU-0012, row index 11, quantity -12)
    first_viol = res.evidence["sample_violations"][0]
    assert first_viol["row_index"] == 11
    assert first_viol["observed_value"] == -12.0


def test_value_range_acceptance_criteria_inventory_corrected(
    corrected_scenario_dir: Path,
) -> None:
    """Verify ValueRangeRule passes on corrected inventory.csv with 0 violations."""
    inventory_csv = corrected_scenario_dir / "inventory.csv"
    assert inventory_csv.is_file()

    ctx = ValidationContext(dataset_id="inventory", file_path=inventory_csv, file_format="csv")
    rule = ValueRangeRule(
        rule_id="VAL-INV-001",
        name="Inventory Non-Negative Check",
        dataset_id="inventory",
        category=RuleCategory.VALUE_RANGE,
        severity=RuleSeverity.HIGH,
        parameters={"column": "quantity_on_hand", "min_value": 0},
    )
    res = rule.evaluate(ctx)

    assert res.status == RuleStatus.PASSED
    assert res.total_record_count == 250
    assert res.affected_record_count == 0


# ---------------------------------------------------------------------------
# 9. Additional Coverage Edge Case Tests
# ---------------------------------------------------------------------------


def test_null_check_more_than_twenty_violations() -> None:
    """Verify NullCheckRule correctly calculates affected count when violations exceed 20."""
    records = [{"id": str(i), "val": None if i < 25 else "valid"} for i in range(30)]
    ctx = ValidationContext(dataset_id="test_ds", records=records)
    rule = NullCheckRule(
        rule_id="NULL-CAP",
        name="Cap Check",
        dataset_id="test_ds",
        category=RuleCategory.NULL_CHECK,
        parameters={"column": "val"},
    )
    res = rule.evaluate(ctx)
    assert res.status == RuleStatus.FAILED
    assert res.affected_record_count == 25
    assert len(res.evidence["sample_violations"]) == 20


def test_type_validity_additional_branches() -> None:
    """Verify boolean rejection in float check and datetime objects in timestamp check."""
    from datetime import UTC, datetime

    # Boolean passed to float check
    ctx_float_bool = ValidationContext(
        dataset_id="t", records=[{"amount": True}, {"amount": False}]
    )
    rule_float = TypeValidityRule(
        rule_id="T-FLT-BOOL",
        name="Float Reject Bool",
        dataset_id="t",
        category=RuleCategory.TYPE_VALIDITY,
        parameters={"column": "amount", "expected_type": "float"},
    )
    assert rule_float.evaluate(ctx_float_bool).affected_record_count == 2

    # Datetime object passed to timestamp check
    ctx_dt = ValidationContext(dataset_id="t", records=[{"ts": datetime(2026, 10, 19, tzinfo=UTC)}])
    rule_ts = TypeValidityRule(
        rule_id="T-DT",
        name="Datetime Object Check",
        dataset_id="t",
        category=RuleCategory.TYPE_VALIDITY,
        parameters={"column": "ts", "expected_type": "timestamp"},
    )
    assert rule_ts.evaluate(ctx_dt).status == RuleStatus.PASSED

    # Boolean object passed to boolean check
    ctx_bool = ValidationContext(dataset_id="t", records=[{"flag": True}, {"flag": False}])
    rule_bool = TypeValidityRule(
        rule_id="T-BOOL-OBJ",
        name="Bool Object Check",
        dataset_id="t",
        category=RuleCategory.TYPE_VALIDITY,
        parameters={"column": "flag", "expected_type": "boolean"},
    )
    assert rule_bool.evaluate(ctx_bool).status == RuleStatus.PASSED

    # String type check
    ctx_str = ValidationContext(dataset_id="t", records=[{"s": "hello"}, {"s": 123}])
    rule_str = TypeValidityRule(
        rule_id="T-STR",
        name="String Check",
        dataset_id="t",
        category=RuleCategory.TYPE_VALIDITY,
        parameters={"column": "s", "expected_type": "string"},
    )
    assert rule_str.evaluate(ctx_str).status == RuleStatus.PASSED


def test_value_range_strict_no_null_and_max_violations() -> None:
    """Verify ValueRangeRule with allow_null=False and max_value boundary checks."""
    # allow_null=False with null
    ctx_null = ValidationContext(dataset_id="t", records=[{"val": None}, {"val": " "}])
    rule_strict = ValueRangeRule(
        rule_id="R-STRICT",
        name="Strict Null Range",
        dataset_id="t",
        category=RuleCategory.VALUE_RANGE,
        parameters={"column": "val", "min_value": 0, "allow_null": False},
    )
    res_strict = rule_strict.evaluate(ctx_null)
    assert res_strict.status == RuleStatus.FAILED
    assert res_strict.affected_record_count == 2

    # max_value violation with inclusive_max=True
    ctx_max = ValidationContext(dataset_id="t", records=[{"val": 50}, {"val": 150}, {"val": 100}])
    rule_max = ValueRangeRule(
        rule_id="R-MAX",
        name="Max Check",
        dataset_id="t",
        category=RuleCategory.VALUE_RANGE,
        parameters={"column": "val", "max_value": 100, "inclusive_max": True},
    )
    res_max = rule_max.evaluate(ctx_max)
    assert res_max.status == RuleStatus.FAILED
    assert res_max.affected_record_count == 1

    # Clean dataset with only min_value (passes)
    ctx_clean_min = ValidationContext(dataset_id="t", records=[{"val": 10}, {"val": 20}])
    rule_clean_min = ValueRangeRule(
        rule_id="R-CLEAN-MIN",
        name="Clean Min",
        dataset_id="t",
        category=RuleCategory.VALUE_RANGE,
        parameters={"column": "val", "min_value": 5},
    )
    assert rule_clean_min.evaluate(ctx_clean_min).status == RuleStatus.PASSED


def test_rule_registry_duck_typed_object_and_list() -> None:
    """Verify RuleRegistry handles duck-typed/SQLAlchemy models and list categories."""

    class MockRuleModel:
        id = "VAL-MOCK-001"
        name = "Mock Rule"
        dataset_id = "orders"
        category = "UNIQUENESS"
        severity = "HIGH"
        parameters = '{"column": "order_id"}'
        description = "Mock description"
        is_active = True

    rule = RuleRegistry.create_rule(MockRuleModel())
    assert isinstance(rule, UniquenessRule)
    assert rule.rule_id == "VAL-MOCK-001"

    # Malformed JSON in parameters falls back to empty dict
    class MockBadJsonModel:
        id = "VAL-BAD-JSON"
        name = "Bad JSON"
        dataset_id = "orders"
        category = "UNIQUENESS"
        severity = "HIGH"
        parameters = "invalid-json"
        description = ""
        is_active = True

    with pytest.raises(ValueError, match="UniquenessRule requires"):
        RuleRegistry.create_rule(MockBadJsonModel())

    # list_registered_categories
    cats = RuleRegistry.list_registered_categories()
    assert "UNIQUENESS" in cats
    assert "NULL_CHECK" in cats
    assert "VALUE_RANGE" in cats
    assert "RECORD_COUNT" in cats
    assert "TYPE_VALIDITY" in cats
