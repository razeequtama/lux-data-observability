"""Unit tests for FreshnessService: partition freshness classification and SLA monitoring."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.pipeline import FreshnessCheck
from app.models.scenario import Scenario
from app.schemas.pipeline import FreshnessStatus
from app.services.pipeline.freshness import FreshnessService


def test_calculate_hours_behind_sunday_orders_delay() -> None:
    """Verify that 18:00:00 vs 23:59:59 yields exactly 5.99 hours behind SLA."""
    expected = datetime(2026, 10, 19, 23, 59, 59, tzinfo=UTC)
    observed = datetime(2026, 10, 19, 18, 0, 0, tzinfo=UTC)

    hours = FreshnessService.calculate_hours_behind(
        expected_timestamp=expected,
        observed_timestamp=observed,
        status="STALE",
    )
    assert hours == 5.99


def test_calculate_hours_behind_fresh_and_on_time() -> None:
    """Verify hours_behind is 0.0 when on time, within tolerance, or marked FRESH."""
    expected = datetime(2026, 10, 19, 23, 59, 59, tzinfo=UTC)
    observed_ahead = datetime(2026, 10, 20, 0, 5, 0, tzinfo=UTC)

    # Observed after expected
    assert (
        FreshnessService.calculate_hours_behind(
            expected_timestamp=expected,
            observed_timestamp=observed_ahead,
        )
        == 0.0
    )

    # Status is explicitly FRESH
    assert (
        FreshnessService.calculate_hours_behind(
            expected_timestamp=expected,
            observed_timestamp=datetime(2026, 10, 19, 18, 0, 0, tzinfo=UTC),
            status=FreshnessStatus.FRESH,
        )
        == 0.0
    )

    # Missing observed timestamp
    assert (
        FreshnessService.calculate_hours_behind(
            expected_timestamp=expected,
            observed_timestamp=None,
        )
        == 0.0
    )


def test_classify_freshness_status_transitions() -> None:
    """Verify classification across FRESH, STALE, and MISSING scenarios."""
    expected = datetime(2026, 10, 19, 23, 59, 59, tzinfo=UTC)

    # 1. Missing timestamp
    status_missing, delay_missing = FreshnessService.classify_freshness(
        expected_timestamp=expected,
        observed_timestamp=None,
    )
    assert status_missing == FreshnessStatus.MISSING
    assert delay_missing == 0.0

    # 2. Within 5-minute tolerance (corrected orders scenario: 23:55:00 vs 23:59:59 = 299s)
    obs_corrected = datetime(2026, 10, 19, 23, 55, 0, tzinfo=UTC)
    status_fresh, delay_fresh = FreshnessService.classify_freshness(
        expected_timestamp=expected,
        observed_timestamp=obs_corrected,
        tolerance_seconds=300.0,
    )
    assert status_fresh == FreshnessStatus.FRESH
    assert delay_fresh == 0.0

    # 3. Beyond tolerance (defective orders scenario: 18:00:00 vs 23:59:59)
    obs_defective = datetime(2026, 10, 19, 18, 0, 0, tzinfo=UTC)
    status_stale, delay_stale = FreshnessService.classify_freshness(
        expected_timestamp=expected,
        observed_timestamp=obs_defective,
    )
    assert status_stale == FreshnessStatus.STALE
    assert delay_stale == 5.99


def test_evaluate_dataset_records() -> None:
    """Verify record-level evaluation handles valid, empty, and malformed rows."""
    expected = datetime(2026, 10, 19, 23, 59, 59, tzinfo=UTC)

    # Empty rows
    status, max_dt, delay = FreshnessService.evaluate_dataset_records(
        records=[],
        timestamp_column="order_date",
        expected_timestamp=expected,
    )
    assert status == FreshnessStatus.MISSING
    assert max_dt is None
    assert delay == 0.0

    # Missing column in records
    status, max_dt, delay = FreshnessService.evaluate_dataset_records(
        records=[{"other_col": "val"}],
        timestamp_column="order_date",
        expected_timestamp=expected,
    )
    assert status == FreshnessStatus.MISSING
    assert max_dt is None

    # Valid records with defective Sunday gap (max at 18:00:00)
    records = [
        {"order_id": "1", "order_date": "2026-10-19T10:00:00Z"},
        {"order_id": "2", "order_date": "2026-10-19T18:00:00Z"},
        {"order_id": "3", "order_date": "invalid-timestamp"},
    ]
    status, max_dt, delay = FreshnessService.evaluate_dataset_records(
        records=records,
        timestamp_column="order_date",
        expected_timestamp=expected,
    )
    assert status == FreshnessStatus.STALE
    assert max_dt == datetime(2026, 10, 19, 18, 0, 0, tzinfo=UTC)
    assert delay == 5.99


def test_evaluate_dataset_file(tmp_path: Path) -> None:
    """Verify evaluation of a CSV file on disk."""
    expected = datetime(2026, 10, 19, 23, 59, 59, tzinfo=UTC)

    # Non-existent file
    status, max_dt, delay = FreshnessService.evaluate_dataset_file(
        file_path=tmp_path / "does_not_exist.csv",
        timestamp_column="order_date",
        expected_timestamp=expected,
    )
    assert status == FreshnessStatus.MISSING

    # Create test CSV
    csv_file = tmp_path / "test_orders.csv"
    csv_file.write_text(
        "order_id,order_date,amount\n"
        "ORD-1,2026-10-19T12:00:00Z,50.0\n"
        "ORD-2,2026-10-19T23:55:00Z,75.0\n",
        encoding="utf-8",
    )

    status, max_dt, delay = FreshnessService.evaluate_dataset_file(
        file_path=csv_file,
        timestamp_column="order_date",
        expected_timestamp=expected,
    )
    assert status == FreshnessStatus.FRESH
    assert max_dt == datetime(2026, 10, 19, 23, 55, 0, tzinfo=UTC)
    assert delay == 0.0


def test_seed_and_get_freshness_checks(db_session: Session) -> None:
    """Verify database persistence, joins with Dataset, and schema conversion."""
    scenario_id = "sc_fresh_test"
    sc = Scenario(id=scenario_id, name="Freshness Scenario")
    db_session.add(sc)

    ds_orders = Dataset(
        id="orders",
        scenario_id=scenario_id,
        name="orders.csv",
        file_path="orders.csv",
        file_format="csv",
        file_size_bytes=1000,
        record_count=100,
        column_count=5,
        schema_definition="{}",
    )
    ds_inv = Dataset(
        id="inventory",
        scenario_id=scenario_id,
        name="inventory.csv",
        file_path="inventory.csv",
        file_format="csv",
        file_size_bytes=500,
        record_count=50,
        column_count=3,
        schema_definition="{}",
    )
    db_session.add_all([ds_orders, ds_inv])
    db_session.flush()

    checks_data = [
        {
            "id": "fresh_ord_1",
            "dataset_id": "orders",
            "expected_partition_timestamp": "2026-10-19T23:59:59Z",
            "observed_partition_timestamp": "2026-10-19T18:00:00Z",
            "sla_hours": 24,
            "status": "STALE",
            "checked_at": "2026-10-20T02:10:00Z",
        },
        {
            "id": "fresh_inv_1",
            "dataset_id": "inventory",
            "expected_partition_timestamp": "2026-10-20T01:00:00Z",
            "observed_partition_timestamp": "2026-10-20T01:30:00Z",
            "sla_hours": 6,
            "status": "FRESH",
            "checked_at": "2026-10-20T02:10:00Z",
        },
    ]

    persisted = FreshnessService.seed_freshness_checks(
        db=db_session,
        scenario_id=scenario_id,
        checks_data=checks_data,
    )
    db_session.commit()
    assert len(persisted) == 2

    # Query via service
    results = FreshnessService.get_freshness_status(db=db_session, scenario_id=scenario_id)
    assert len(results) == 2

    ord_res = next(r for r in results if r.dataset_id == "orders")
    assert ord_res.dataset_name == "orders.csv"
    assert ord_res.status == FreshnessStatus.STALE
    assert ord_res.hours_behind == 5.99
    assert ord_res.sla_hours == 24

    inv_res = next(r for r in results if r.dataset_id == "inventory")
    assert inv_res.dataset_name == "inventory.csv"
    assert inv_res.status == FreshnessStatus.FRESH
    assert inv_res.hours_behind == 0.0

    # Filter by single dataset_id
    filtered = FreshnessService.get_freshness_status(
        db=db_session, scenario_id=scenario_id, dataset_id="orders"
    )
    assert len(filtered) == 1
    assert filtered[0].dataset_id == "orders"


def test_missing_timestamp_check(db_session: Session) -> None:
    """Verify handling when observed_partition_timestamp is None."""
    scenario_id = "sc_fresh_missing"
    sc = Scenario(id=scenario_id, name="Missing Scenario")
    db_session.add(sc)

    ds = Dataset(
        id="missing_ds",
        scenario_id=scenario_id,
        name="missing.csv",
        file_path="missing.csv",
        file_format="csv",
        file_size_bytes=100,
        record_count=0,
        column_count=1,
        schema_definition="{}",
    )
    db_session.add(ds)
    db_session.flush()

    check = FreshnessCheck(
        id="fresh_missing_001",
        scenario_id=scenario_id,
        dataset_id=ds.id,
        expected_partition_timestamp=datetime(2026, 10, 20, 0, 0, 0, tzinfo=UTC),
        observed_partition_timestamp=None,
        sla_hours=12,
        status="MISSING",
    )
    db_session.add(check)
    db_session.commit()

    results = FreshnessService.get_freshness_status(db=db_session, scenario_id=scenario_id)
    assert len(results) == 1
    assert results[0].status == FreshnessStatus.MISSING
    assert results[0].observed_partition_timestamp is None
    assert results[0].hours_behind == 0.0
