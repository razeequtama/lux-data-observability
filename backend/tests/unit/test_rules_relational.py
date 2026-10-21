"""Unit tests for relational, temporal, schema, and freshness rule evaluators.

Acceptance Criteria:
1. ReferentialIntegrityRule detects 24 orphaned items in order_items.csv missing from products.csv.
2. TemporalAnomalyRule detects Sunday evening transaction gap in orders.csv.
3. Unit tests pass with 100% assertions satisfied.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import settings
from app.schemas.validation import (
    RuleCategory,
    RuleSeverity,
    RuleStatus,
    ValidationRuleConfig,
)
from app.services.validation.base import ValidationContext
from app.services.validation.registry import RuleRegistry
from app.services.validation.relational import (
    FreshnessRule,
    ReferentialIntegrityRule,
    SchemaIntegrityRule,
    TemporalAnomalyRule,
)


@pytest.fixture
def defective_dir() -> Path:
    """Fixture providing path to defective scenario fixtures."""
    path = settings.scenarios_dir / "monday_revenue_mystery" / "defective"
    assert path.is_dir()
    return path


@pytest.fixture
def corrected_dir() -> Path:
    """Fixture providing path to corrected scenario fixtures."""
    path = settings.scenarios_dir / "monday_revenue_mystery" / "corrected"
    assert path.is_dir()
    return path


# ===========================================================================
# 1. ReferentialIntegrityRule Tests & Signature Acceptance Criteria
# ===========================================================================


def test_referential_integrity_signature_defective_acceptance_criterion(
    defective_dir: Path,
) -> None:
    """Acceptance Criterion 1: Detect exactly 24 orphaned items in defective order_items.csv."""
    items_file = defective_dir / "order_items.csv"
    prods_file = defective_dir / "products.csv"

    # Context streaming order_items with products as sibling file resolution
    ctx = ValidationContext(
        dataset_id="order_items",
        file_path=items_file,
        file_format="csv",
        datasets={"products": prods_file},
    )

    rule = ReferentialIntegrityRule(
        rule_id="VAL-ORD-002",
        name="Order Items Foreign Key Check",
        dataset_id="order_items",
        category=RuleCategory.REFERENTIAL_INTEGRITY,
        severity=RuleSeverity.HIGH,
        parameters={
            "column": "product_id",
            "parent_dataset": "products",
            "parent_column": "product_id",
        },
    )

    result = rule.evaluate(ctx)

    assert result.status == RuleStatus.FAILED
    assert result.affected_record_count == 24
    assert result.total_record_count == 3420
    assert "24 orphaned record(s)" in result.message
    assert result.evidence["parent_dataset"] == "products"
    assert result.evidence["parent_key_count"] == 250
    assert result.evidence["total_orphaned_records"] == 24

    orphaned_keys = result.evidence["sample_orphaned_keys"]
    assert len(orphaned_keys) == 24
    # Fixtures introduce PRD-9001 through PRD-9024
    assert "PRD-9001" in orphaned_keys
    assert "PRD-9024" in orphaned_keys

    # Check sample violations
    samples = result.evidence["sample_violations"]
    assert len(samples) == 24
    assert all("PRD-90" in s["foreign_key_value"] for s in samples)


def test_referential_integrity_signature_corrected_acceptance_criterion(
    corrected_dir: Path,
) -> None:
    """Acceptance Criterion 1 Recovery: 0 orphaned items in corrected order_items.csv."""
    items_file = corrected_dir / "order_items.csv"
    prods_file = corrected_dir / "products.csv"

    ctx = ValidationContext(
        dataset_id="order_items",
        file_path=items_file,
        file_format="csv",
        datasets={"products": prods_file},
    )

    rule = ReferentialIntegrityRule(
        rule_id="VAL-ORD-002",
        name="Order Items Foreign Key Check",
        dataset_id="order_items",
        category=RuleCategory.REFERENTIAL_INTEGRITY,
        parameters={
            "column": "product_id",
            "parent_dataset": "products",
            "parent_column": "product_id",
        },
    )

    result = rule.evaluate(ctx)

    assert result.status == RuleStatus.PASSED
    assert result.affected_record_count == 0
    assert result.total_record_count == 3420
    assert "satisfy referential integrity" in result.message
    assert result.evidence["parent_key_count"] == 250


def test_referential_integrity_in_memory_pass() -> None:
    """Test ReferentialIntegrityRule on clean in-memory datasets."""
    parent_data = [{"id": "P1", "name": "Prod A"}, {"id": "P2", "name": "Prod B"}]
    child_data = [
        {"item": "I1", "product_id": "P1"},
        {"item": "I2", "product_id": "P2"},
        {"item": "I3", "product_id": "P1"},
    ]

    ctx = ValidationContext(
        dataset_id="child_items",
        records=child_data,
        datasets={"parent_prods": parent_data},
    )

    rule = ReferentialIntegrityRule(
        rule_id="R-FK-01",
        name="FK Test",
        dataset_id="child_items",
        category=RuleCategory.REFERENTIAL_INTEGRITY,
        parameters={
            "column": "product_id",
            "parent_dataset": "parent_prods",
            "parent_column": "id",
        },
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.PASSED
    assert result.affected_record_count == 0


def test_referential_integrity_in_memory_orphans() -> None:
    """Test ReferentialIntegrityRule detecting orphaned rows in-memory."""
    parent_data = [{"id": "P1"}]
    child_data = [
        {"item": "I1", "product_id": "P1"},
        {"item": "I2", "product_id": "P999"},
        {"item": "I3", "product_id": "P888"},
    ]

    ctx = ValidationContext(
        dataset_id="child_items",
        records=child_data,
        datasets={"parent_prods": parent_data},
    )

    rule = ReferentialIntegrityRule(
        rule_id="R-FK-02",
        name="FK Orphan Test",
        dataset_id="child_items",
        category=RuleCategory.REFERENTIAL_INTEGRITY,
        parameters={
            "column": "product_id",
            "parent_dataset": "parent_prods",
            "parent_column": "id",
        },
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.FAILED
    assert result.affected_record_count == 2
    assert "P999" in result.evidence["sample_orphaned_keys"]
    assert "P888" in result.evidence["sample_orphaned_keys"]


def test_referential_integrity_allow_null() -> None:
    """Test ReferentialIntegrityRule with allow_null parameter."""
    parent_data = [{"id": "P1"}]
    child_data = [
        {"item": "I1", "product_id": "P1"},
        {"item": "I2", "product_id": None},
        {"item": "I3", "product_id": "   "},
    ]

    # When allow_null is True: null foreign keys are skipped
    ctx = ValidationContext(
        dataset_id="child_items",
        records=child_data,
        datasets={"parent_prods": parent_data},
    )

    rule_allow = ReferentialIntegrityRule(
        rule_id="R-FK-03",
        name="FK Allow Null",
        dataset_id="child_items",
        category=RuleCategory.REFERENTIAL_INTEGRITY,
        parameters={
            "column": "product_id",
            "parent_dataset": "parent_prods",
            "parent_column": "id",
            "allow_null": True,
        },
    )
    result_allow = rule_allow.evaluate(ctx)
    assert result_allow.status == RuleStatus.PASSED

    # When allow_null is False: null foreign keys violate integrity
    rule_disallow = ReferentialIntegrityRule(
        rule_id="R-FK-04",
        name="FK Disallow Null",
        dataset_id="child_items",
        category=RuleCategory.REFERENTIAL_INTEGRITY,
        parameters={
            "column": "product_id",
            "parent_dataset": "parent_prods",
            "parent_column": "id",
            "allow_null": False,
        },
    )
    result_disallow = rule_disallow.evaluate(ctx)
    assert result_disallow.status == RuleStatus.FAILED
    assert result_disallow.affected_record_count == 2


def test_referential_integrity_composite_keys() -> None:
    """Test ReferentialIntegrityRule with composite foreign keys."""
    parent_data = [
        {"tenant_id": "T1", "user_id": "U100"},
        {"tenant_id": "T1", "user_id": "U200"},
    ]
    child_data = [
        {"log_id": "L1", "tenant": "T1", "user": "U100"},
        {"log_id": "L2", "tenant": "T1", "user": "U999"},  # Invalid
        {"log_id": "L3", "tenant": "T2", "user": "U100"},  # Invalid
    ]

    ctx = ValidationContext(
        dataset_id="logs",
        records=child_data,
        datasets={"tenants": parent_data},
    )

    rule = ReferentialIntegrityRule(
        rule_id="R-FK-COMP",
        name="Composite FK Test",
        dataset_id="logs",
        category=RuleCategory.REFERENTIAL_INTEGRITY,
        parameters={
            "column": ["tenant", "user"],
            "parent_dataset": "tenants",
            "parent_column": ["tenant_id", "user_id"],
        },
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.FAILED
    assert result.affected_record_count == 2


def test_referential_integrity_missing_parent_dataset_error() -> None:
    """Test ReferentialIntegrityRule returns ERROR status if parent dataset cannot be resolved."""
    ctx = ValidationContext(dataset_id="items", records=[{"id": "1", "pid": "P1"}])

    rule = ReferentialIntegrityRule(
        rule_id="R-FK-ERR",
        name="FK Missing Parent",
        dataset_id="items",
        category=RuleCategory.REFERENTIAL_INTEGRITY,
        parameters={
            "column": "pid",
            "parent_dataset": "non_existent_dataset",
            "parent_column": "id",
        },
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.ERROR
    assert "could not be resolved" in result.message


def test_referential_integrity_parameter_validation() -> None:
    """Test ReferentialIntegrityRule validates input parameters on initialization."""
    with pytest.raises(ValueError, match="requires 'column' parameter"):
        ReferentialIntegrityRule(
            rule_id="R1",
            name="Test",
            dataset_id="ds",
            category=RuleCategory.REFERENTIAL_INTEGRITY,
            parameters={"parent_dataset": "p"},
        )

    with pytest.raises(ValueError, match="requires 'parent_dataset' parameter"):
        ReferentialIntegrityRule(
            rule_id="R2",
            name="Test",
            dataset_id="ds",
            category=RuleCategory.REFERENTIAL_INTEGRITY,
            parameters={"column": "c"},
        )

    with pytest.raises(ValueError, match="column count"):
        ReferentialIntegrityRule(
            rule_id="R3",
            name="Test",
            dataset_id="ds",
            category=RuleCategory.REFERENTIAL_INTEGRITY,
            parameters={
                "column": ["c1", "c2"],
                "parent_dataset": "p",
                "parent_column": ["p1"],
            },
        )


# ===========================================================================
# 2. TemporalAnomalyRule Tests & Signature Acceptance Criteria
# ===========================================================================


def test_temporal_anomaly_signature_defective_gap_acceptance_criterion(
    defective_dir: Path,
) -> None:
    """Acceptance Criterion 2: Detect Sunday evening transaction gap in defective orders.csv."""
    orders_file = defective_dir / "orders.csv"
    ctx = ValidationContext(dataset_id="orders", file_path=orders_file, file_format="csv")

    rule = TemporalAnomalyRule(
        rule_id="VAL-TEMP-001",
        name="Sunday Orders Temporal Gap Check",
        dataset_id="orders",
        category=RuleCategory.TEMPORAL_ANOMALY,
        severity=RuleSeverity.MEDIUM,
        parameters={
            "column": "order_date",
            "max_gap_hours": 4.0,
            # Set reference time to after orders window so future check doesn't trigger
            "now_reference": "2026-10-21T00:00:00Z",
        },
    )

    result = rule.evaluate(ctx)

    assert result.status == RuleStatus.FAILED
    assert result.affected_record_count >= 1
    assert "temporal gap(s) exceeding 4.0h threshold" in result.message

    gaps = result.evidence["temporal_gaps"]
    assert len(gaps) == 1
    gap = gaps[0]
    # Sunday gap: from 2026-10-18T17:58:01 to 2026-10-18T22:26:00 (4.47 hours)
    assert gap["gap_hours"] == pytest.approx(4.47, 0.05)
    assert "2026-10-18T17:58:01" in gap["gap_start"]
    assert "2026-10-18T22:26:00" in gap["gap_end"]
    assert result.evidence["max_observed_gap_hours"] == pytest.approx(4.47, 0.05)


def test_temporal_anomaly_signature_corrected_acceptance_criterion(
    corrected_dir: Path,
) -> None:
    """Acceptance Criterion 2 Recovery: Temporal gap resolved in corrected orders.csv."""
    orders_file = corrected_dir / "orders.csv"
    ctx = ValidationContext(dataset_id="orders", file_path=orders_file, file_format="csv")

    rule = TemporalAnomalyRule(
        rule_id="VAL-TEMP-001",
        name="Sunday Orders Temporal Gap Check",
        dataset_id="orders",
        category=RuleCategory.TEMPORAL_ANOMALY,
        parameters={
            "column": "order_date",
            "max_gap_hours": 4.0,
            "now_reference": "2026-10-21T00:00:00Z",
        },
    )

    result = rule.evaluate(ctx)

    assert result.status == RuleStatus.PASSED
    assert result.affected_record_count == 0
    # In corrected data, maximum gap is only 0.68 hours (< 4.0h)
    assert result.evidence["max_observed_gap_hours"] < 1.0


def test_temporal_anomaly_future_timestamp_detection() -> None:
    """Test TemporalAnomalyRule detecting future timestamps."""
    records = [
        {"id": "1", "ts": "2026-10-15T10:00:00Z"},
        {"id": "2", "ts": "2026-10-25T12:00:00Z"},  # Future relative to ref
        {"id": "3", "ts": "2026-10-16T11:00:00Z"},
    ]
    ctx = ValidationContext(dataset_id="events", records=records)

    rule = TemporalAnomalyRule(
        rule_id="TEMP-FUT",
        name="No Future Events",
        dataset_id="events",
        category=RuleCategory.TEMPORAL_ANOMALY,
        parameters={
            "column": "ts",
            "allow_future": False,
            "now_reference": "2026-10-20T00:00:00Z",
        },
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.FAILED
    assert result.affected_record_count == 1
    assert "future timestamp(s)" in result.message
    assert len(result.evidence["sample_future_records"]) == 1


def test_temporal_anomaly_unparseable_timestamp_detection() -> None:
    """Test TemporalAnomalyRule detecting unparseable timestamp strings."""
    records = [
        {"id": "1", "ts": "2026-10-15T10:00:00Z"},
        {"id": "2", "ts": "invalid-datetime-string"},
        {"id": "3", "ts": "2026-10-16T11:00:00Z"},
    ]
    ctx = ValidationContext(dataset_id="events", records=records)

    rule = TemporalAnomalyRule(
        rule_id="TEMP-PARSE",
        name="Parseable Timestamps",
        dataset_id="events",
        category=RuleCategory.TEMPORAL_ANOMALY,
        parameters={"column": "ts", "now_reference": "2026-10-20T00:00:00Z"},
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.FAILED
    assert "unparseable timestamp(s)" in result.message
    assert len(result.evidence["sample_unparseable_records"]) == 1


def test_temporal_anomaly_bounds_check() -> None:
    """Test TemporalAnomalyRule min_date and max_date checks."""
    records = [
        {"id": "1", "ts": "2026-10-01T00:00:00Z"},  # Too early
        {"id": "2", "ts": "2026-10-15T00:00:00Z"},
        {"id": "3", "ts": "2026-10-20T00:00:00Z"},  # Too late
    ]
    ctx = ValidationContext(dataset_id="events", records=records)

    rule = TemporalAnomalyRule(
        rule_id="TEMP-BOUNDS",
        name="Bounds Test",
        dataset_id="events",
        category=RuleCategory.TEMPORAL_ANOMALY,
        parameters={
            "column": "ts",
            "min_date": "2026-10-10T00:00:00Z",
            "max_date": "2026-10-18T00:00:00Z",
            "allow_future": True,
        },
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.FAILED
    assert result.affected_record_count == 2
    assert "out-of-range" in result.message


# ===========================================================================
# 3. SchemaIntegrityRule Tests
# ===========================================================================


def test_schema_integrity_exact_match_pass(defective_dir: Path) -> None:
    """Test SchemaIntegrityRule passes when columns and types match."""
    prods_file = defective_dir / "products.csv"
    ctx = ValidationContext(dataset_id="products", file_path=prods_file, file_format="csv")

    rule = SchemaIntegrityRule(
        rule_id="VAL-SCHEMA-001",
        name="Products Schema Check",
        dataset_id="products",
        category=RuleCategory.SCHEMA_INTEGRITY,
        parameters={
            "expected_columns": [
                {"name": "product_id", "type": "string"},
                {"name": "sku", "type": "string"},
                {"name": "category", "type": "string"},
                {"name": "base_price", "type": "float"},
            ]
        },
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.PASSED
    assert result.affected_record_count == 0
    assert "satisfies schema integrity requirements" in result.message


def test_schema_integrity_missing_columns() -> None:
    """Test SchemaIntegrityRule detecting missing columns."""
    records = [{"order_id": "ORD-1", "customer_id": "CUST-1"}]
    ctx = ValidationContext(dataset_id="orders", records=records)

    rule = SchemaIntegrityRule(
        rule_id="SCHEMA-MISSING",
        name="Orders Schema",
        dataset_id="orders",
        category=RuleCategory.SCHEMA_INTEGRITY,
        parameters={"expected_columns": ["order_id", "customer_id", "order_date", "total_amount"]},
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.FAILED
    assert "missing 2 column(s)" in result.message
    assert "order_date" in result.evidence["missing_columns"]
    assert "total_amount" in result.evidence["missing_columns"]


def test_schema_integrity_unexpected_columns_disallowed() -> None:
    """Test SchemaIntegrityRule detecting unexpected columns when allow_extra_columns=False."""
    records = [{"id": "1", "name": "A", "unexpected_field": "leak"}]
    ctx = ValidationContext(dataset_id="users", records=records)

    rule = SchemaIntegrityRule(
        rule_id="SCHEMA-EXTRA",
        name="Strict Users Schema",
        dataset_id="users",
        category=RuleCategory.SCHEMA_INTEGRITY,
        parameters={
            "expected_columns": ["id", "name"],
            "allow_extra_columns": False,
        },
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.FAILED
    assert "unexpected_field" in result.evidence["unexpected_columns"]


def test_schema_integrity_strict_order_mismatch() -> None:
    """Test SchemaIntegrityRule detecting column ordering mismatch when strict_order=True."""
    records = [{"col_b": "2", "col_a": "1"}]
    ctx = ValidationContext(dataset_id="ordered_table", records=records)

    rule = SchemaIntegrityRule(
        rule_id="SCHEMA-ORDER",
        name="Strict Column Order",
        dataset_id="ordered_table",
        category=RuleCategory.SCHEMA_INTEGRITY,
        parameters={
            "expected_columns": ["col_a", "col_b"],
            "strict_order": True,
        },
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.FAILED
    assert "column ordering" in result.message


def test_schema_integrity_type_drift_detection() -> None:
    """Test SchemaIntegrityRule detecting type drift (e.g. non-numeric in float column)."""
    records = [
        {"item_id": "1", "quantity": "10", "price": "19.99"},
        {"item_id": "2", "quantity": "invalid_int", "price": "29.99"},
        {"item_id": "3", "quantity": "15", "price": "not_a_number"},
    ]
    ctx = ValidationContext(dataset_id="items", records=records)

    rule = SchemaIntegrityRule(
        rule_id="SCHEMA-TYPES",
        name="Items Type Check",
        dataset_id="items",
        category=RuleCategory.SCHEMA_INTEGRITY,
        parameters={
            "expected_columns": ["item_id", "quantity", "price"],
            "expected_types": {"quantity": "integer", "price": "float"},
        },
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.FAILED
    assert len(result.evidence["type_mismatches"]) == 2


# ===========================================================================
# 4. FreshnessRule Tests
# ===========================================================================


def test_freshness_rule_signature_defective_gap_acceptance(defective_dir: Path) -> None:
    """Test FreshnessRule evaluates VAL-FRESH-001 on defective orders.csv."""
    orders_file = defective_dir / "orders.csv"
    ctx = ValidationContext(dataset_id="orders", file_path=orders_file, file_format="csv")

    rule = FreshnessRule(
        rule_id="VAL-FRESH-001",
        name="Partition Freshness Check",
        dataset_id="orders",
        category=RuleCategory.FRESHNESS,
        severity=RuleSeverity.MEDIUM,
        parameters={
            "column": "order_date",
            "sla_hours": 24,
            "max_gap_hours": 4,
        },
    )

    result = rule.evaluate(ctx)

    assert result.status == RuleStatus.FAILED
    assert "Partition freshness violation" in result.message
    assert result.evidence["status"] == "STALE"
    assert result.evidence["max_gap_hours"] == 4.0
    assert result.evidence["observed_max_gap_hours"] == pytest.approx(4.47, 0.05)
    assert len(result.evidence["gap_violations"]) >= 1


def test_freshness_rule_signature_corrected_acceptance(corrected_dir: Path) -> None:
    """Test FreshnessRule evaluates VAL-FRESH-001 on corrected orders.csv."""
    orders_file = corrected_dir / "orders.csv"
    ctx = ValidationContext(dataset_id="orders", file_path=orders_file, file_format="csv")

    rule = FreshnessRule(
        rule_id="VAL-FRESH-001",
        name="Partition Freshness Check",
        dataset_id="orders",
        category=RuleCategory.FRESHNESS,
        parameters={
            "column": "order_date",
            "sla_hours": 24,
            "max_gap_hours": 4,
        },
    )

    result = rule.evaluate(ctx)

    assert result.status == RuleStatus.PASSED
    assert result.evidence["status"] == "FRESH"
    assert result.evidence["observed_max_gap_hours"] < 1.0


def test_freshness_rule_sla_delay_breach() -> None:
    """Test FreshnessRule flags stale partitions exceeding SLA hours."""
    records = [
        {"id": "1", "updated_at": "2026-10-18T10:00:00Z"},
        {"id": "2", "updated_at": "2026-10-18T12:00:00Z"},
    ]
    ctx = ValidationContext(dataset_id="metrics", records=records)

    # Reference time is 2026-10-20T00:00:00Z (36 hours after latest record)
    # SLA threshold is 24 hours
    rule = FreshnessRule(
        rule_id="FRESH-SLA",
        name="Daily Metrics Freshness",
        dataset_id="metrics",
        category=RuleCategory.FRESHNESS,
        parameters={
            "column": "updated_at",
            "sla_hours": 24,
            "expected_partition_timestamp": "2026-10-20T00:00:00Z",
        },
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.FAILED
    assert result.evidence["status"] == "STALE"
    assert result.evidence["hours_behind"] == pytest.approx(36.0, 0.1)


def test_freshness_rule_warn_only() -> None:
    """Test FreshnessRule produces WARNING status when warn_only is True."""
    records = [{"id": "1", "updated_at": "2026-10-18T10:00:00Z"}]
    ctx = ValidationContext(dataset_id="metrics", records=records)

    rule = FreshnessRule(
        rule_id="FRESH-WARN",
        name="Metrics Freshness Warning",
        dataset_id="metrics",
        category=RuleCategory.FRESHNESS,
        parameters={
            "column": "updated_at",
            "sla_hours": 12,
            "expected_partition_timestamp": "2026-10-20T00:00:00Z",
            "warn_only": True,
        },
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.WARNING


def test_freshness_rule_missing_timestamps() -> None:
    """Test FreshnessRule fails gracefully when no timestamps exist."""
    records = [{"id": "1", "updated_at": None}, {"id": "2", "updated_at": ""}]
    ctx = ValidationContext(dataset_id="empty_ts", records=records)

    rule = FreshnessRule(
        rule_id="FRESH-MISSING",
        name="Empty Timestamp Check",
        dataset_id="empty_ts",
        category=RuleCategory.FRESHNESS,
        parameters={"column": "updated_at"},
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.FAILED
    assert result.evidence["status"] == "MISSING"


# ===========================================================================
# 5. RuleRegistry Integration Tests for Advanced Rules
# ===========================================================================


def test_rule_registry_instantiates_advanced_rules() -> None:
    """Test RuleRegistry dynamic factory instantiates all 4 advanced rule types."""
    # 1. Referential Integrity
    r1 = RuleRegistry.create_rule(
        ValidationRuleConfig(
            id="R1",
            dataset_id="order_items",
            name="FK Check",
            category=RuleCategory.REFERENTIAL_INTEGRITY,
            parameters={"column": "product_id", "parent_dataset": "products"},
        )
    )
    assert isinstance(r1, ReferentialIntegrityRule)

    # 2. Temporal Anomaly
    r2 = RuleRegistry.create_rule(
        {
            "id": "R2",
            "dataset_id": "orders",
            "name": "Temporal Check",
            "category": "TEMPORAL_ANOMALY",
            "parameters": {"column": "order_date"},
        }
    )
    assert isinstance(r2, TemporalAnomalyRule)

    # 3. Schema Integrity
    r3 = RuleRegistry.create_rule(
        ValidationRuleConfig(
            id="R3",
            dataset_id="inventory",
            name="Schema Check",
            category=RuleCategory.SCHEMA_INTEGRITY,
            parameters={"expected_columns": ["sku", "warehouse_id"]},
        )
    )
    assert isinstance(r3, SchemaIntegrityRule)

    # 4. Freshness
    r4 = RuleRegistry.create_rule(
        {
            "id": "R4",
            "dataset_id": "orders",
            "name": "Freshness Check",
            "category": "FRESHNESS",
            "parameters": {"column": "order_date", "sla_hours": 24},
        }
    )
    assert isinstance(r4, FreshnessRule)


def test_inactive_advanced_rule_skipped() -> None:
    """Test that inactive rules return SKIPPED status."""
    ctx = ValidationContext(dataset_id="test", records=[{"a": 1}])
    rule = ReferentialIntegrityRule(
        rule_id="R-INACTIVE",
        name="Inactive FK Check",
        dataset_id="test",
        category=RuleCategory.REFERENTIAL_INTEGRITY,
        parameters={"column": "a", "parent_dataset": "p"},
        is_active=False,
    )

    result = rule.evaluate(ctx)
    assert result.status == RuleStatus.SKIPPED
    assert "skipped" in result.message
