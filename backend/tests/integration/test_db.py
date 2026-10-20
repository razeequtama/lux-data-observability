"""Integration tests for SQLite persistence, WAL mode, schema tables, constraints, and cascades."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.models import (
    Dataset,
    FreshnessCheck,
    Investigation,
    LineageEdge,
    LineageNode,
    PipelineRun,
    ReportArtifact,
    Scenario,
    ValidationFinding,
    ValidationRule,
    ValidationRun,
)

EXPECTED_TABLES = {
    "scenarios",
    "datasets",
    "validation_rules",
    "validation_runs",
    "validation_findings",
    "lineage_nodes",
    "lineage_edges",
    "pipeline_runs",
    "freshness_checks",
    "investigations",
    "report_artifacts",
}


def test_sqlite_pragmas(tmp_db_engine: Engine) -> None:
    """Verify that SQLite connection applies WAL journal mode, foreign keys, and busy timeout."""
    with tmp_db_engine.connect() as conn:
        journal_mode = conn.execute(text("PRAGMA journal_mode")).scalar()
        foreign_keys = conn.execute(text("PRAGMA foreign_keys")).scalar()
        busy_timeout = conn.execute(text("PRAGMA busy_timeout")).scalar()

    assert str(journal_mode).lower() == "wal"
    assert foreign_keys == 1
    assert busy_timeout == 5000


def test_all_11_tables_and_indices_created(tmp_db_engine: Engine) -> None:
    """Verify that all 11 domain tables and their declared indices exist in the database."""
    inspector = inspect(tmp_db_engine)
    existing_tables = set(inspector.get_table_names())

    assert EXPECTED_TABLES.issubset(existing_tables)
    assert len(EXPECTED_TABLES) == 11

    # Verify declared indices on tables
    def get_index_names(table_name: str) -> set[str]:
        return {idx["name"] for idx in inspector.get_indexes(table_name)}

    assert "idx_datasets_scenario" in get_index_names("datasets")
    assert {"idx_rules_scenario", "idx_rules_dataset"}.issubset(get_index_names("validation_rules"))
    assert "idx_val_runs_scenario" in get_index_names("validation_runs")
    assert {"idx_findings_run", "idx_findings_rule", "idx_findings_dataset"}.issubset(
        get_index_names("validation_findings")
    )
    assert "idx_nodes_scenario" in get_index_names("lineage_nodes")
    assert {"idx_edges_scenario", "idx_edges_source", "idx_edges_target"}.issubset(
        get_index_names("lineage_edges")
    )
    assert "idx_pipeline_runs_scenario" in get_index_names("pipeline_runs")
    assert "idx_reports_investigation" in get_index_names("report_artifacts")


def test_entity_crud_and_relationships(db_session: Session) -> None:
    """Verify complete CRUD and bidirectional relationship navigation across all 11 entities."""
    now = datetime.now(UTC)

    # 1. Create Scenario
    scenario = Scenario(
        id="test_scenario",
        name="Test Observability Scenario",
        description="Scenario for persistence testing",
        category="e-commerce",
        is_bundled=True,
        active_fixture_version="defective",
    )
    db_session.add(scenario)
    db_session.flush()

    # 2. Create Datasets
    orders_ds = Dataset(
        id="ds_orders",
        scenario_id=scenario.id,
        name="orders.csv",
        file_path="scenarios/test/orders.csv",
        file_format="csv",
        file_size_bytes=10240,
        record_count=100,
        column_count=5,
        schema_definition=json.dumps([{"name": "order_id", "type": "string"}]),
    )
    items_ds = Dataset(
        id="ds_items",
        scenario_id=scenario.id,
        name="order_items.csv",
        file_path="scenarios/test/order_items.csv",
        file_format="csv",
        file_size_bytes=20480,
        record_count=300,
        column_count=4,
        schema_definition=json.dumps([{"name": "item_id", "type": "string"}]),
    )
    db_session.add_all([orders_ds, items_ds])
    db_session.flush()

    # 3. Create Validation Rule
    rule = ValidationRule(
        id="rule_unique_order_id",
        scenario_id=scenario.id,
        dataset_id=orders_ds.id,
        name="Unique Order IDs",
        category="UNIQUENESS",
        severity="CRITICAL",
        parameters=json.dumps({"column": "order_id"}),
        is_active=True,
    )
    db_session.add(rule)
    db_session.flush()

    # 4. Create Validation Run
    val_run = ValidationRun(
        id="run_001",
        scenario_id=scenario.id,
        fixture_version="defective",
        status="FAILED",
        total_checks=1,
        passed_checks=0,
        failed_checks=1,
        warning_checks=0,
        skipped_checks=0,
        error_checks=0,
        execution_duration_ms=45,
    )
    db_session.add(val_run)
    db_session.flush()

    # 5. Create Validation Finding
    finding = ValidationFinding(
        id="finding_001",
        run_id=val_run.id,
        rule_id=rule.id,
        dataset_id=orders_ds.id,
        rule_category="UNIQUENESS",
        severity="CRITICAL",
        status="FAILED",
        affected_fields=json.dumps(["order_id"]),
        affected_record_count=15,
        total_record_count=100,
        message="Found 15 duplicate order IDs",
        evidence=json.dumps({"duplicate_ids": ["ORD-1", "ORD-2"]}),
        execution_duration_ms=12,
    )
    db_session.add(finding)
    db_session.flush()

    # 6. Create Lineage Nodes & Edge
    node_src = LineageNode(
        id="node_src_orders",
        scenario_id=scenario.id,
        name="orders.csv",
        node_type="SOURCE_DATASET",
        dataset_id=orders_ds.id,
        owner="Data Platform",
        description="Source orders table",
        node_metadata=json.dumps({"format": "csv"}),
    )
    node_tf = LineageNode(
        id="node_tf_orders",
        scenario_id=scenario.id,
        name="transform_orders",
        node_type="TRANSFORMATION",
        dataset_id=None,
        owner="Analytics Team",
        description="Cleaning transform",
        node_metadata=json.dumps({"engine": "SQL"}),
    )
    db_session.add_all([node_src, node_tf])
    db_session.flush()

    edge = LineageEdge(
        id="edge_src_to_tf",
        scenario_id=scenario.id,
        source_id=node_src.id,
        target_id=node_tf.id,
        dependency_type="DIRECT_INPUT",
    )
    db_session.add(edge)
    db_session.flush()

    # 7. Create Pipeline Run
    pipe_run = PipelineRun(
        id="pipe_run_001",
        scenario_id=scenario.id,
        pipeline_name="daily_orders_etl",
        execution_status="COMPLETED_SUCCESS",
        quality_health="CORRUPTED",
        start_time=now,
        end_time=now,
        duration_ms=12000,
        records_ingested=100,
        records_written=100,
        error_message=None,
        run_log=json.dumps(["Step 1: Ingested", "Step 2: Written"]),
    )
    db_session.add(pipe_run)
    db_session.flush()

    # 8. Create Freshness Check
    freshness = FreshnessCheck(
        id="fresh_001",
        scenario_id=scenario.id,
        dataset_id=orders_ds.id,
        expected_partition_timestamp=now,
        observed_partition_timestamp=now,
        sla_hours=24,
        status="FRESH",
    )
    db_session.add(freshness)
    db_session.flush()

    # 9. Create Investigation
    investigation = Investigation(
        id="inv_001",
        scenario_id=scenario.id,
        title="Monday Revenue Discrepancy",
        status="INVESTIGATING",
        initial_finding_id=finding.id,
        verified_facts=json.dumps(["Pipeline completed return code 0", "Duplicate order IDs"]),
        hypotheses=json.dumps(["Upstream webhook retried payload"]),
        action_items=json.dumps(["Deduplicate incoming batches"]),
    )
    db_session.add(investigation)
    db_session.flush()

    # 10. Create Report Artifact
    report = ReportArtifact(
        id="rep_001",
        investigation_id=investigation.id,
        scenario_id=scenario.id,
        validation_run_id=val_run.id,
        format="html",
        file_path="artifacts/report_001.html",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        file_size_bytes=4096,
    )
    db_session.add(report)
    db_session.commit()

    # Expire and reload to test relationship navigation
    db_session.expire_all()

    loaded_scenario = db_session.get(Scenario, scenario.id)
    assert loaded_scenario is not None
    assert len(loaded_scenario.datasets) == 2
    assert len(loaded_scenario.validation_rules) == 1
    assert len(loaded_scenario.validation_runs) == 1
    assert len(loaded_scenario.lineage_nodes) == 2
    assert len(loaded_scenario.lineage_edges) == 1
    assert len(loaded_scenario.pipeline_runs) == 1
    assert len(loaded_scenario.freshness_checks) == 1
    assert len(loaded_scenario.investigations) == 1
    assert len(loaded_scenario.report_artifacts) == 1

    # Test reverse / child navigation
    loaded_run = db_session.get(ValidationRun, val_run.id)
    assert loaded_run is not None
    assert len(loaded_run.findings) == 1
    assert loaded_run.findings[0].message == "Found 15 duplicate order IDs"

    loaded_src = db_session.get(LineageNode, node_src.id)
    assert loaded_src is not None
    assert len(loaded_src.outgoing_edges) == 1
    assert loaded_src.outgoing_edges[0].target_id == node_tf.id

    loaded_tf = db_session.get(LineageNode, node_tf.id)
    assert loaded_tf is not None
    assert len(loaded_tf.incoming_edges) == 1
    assert loaded_tf.incoming_edges[0].source_id == node_src.id

    loaded_inv = db_session.get(Investigation, investigation.id)
    assert loaded_inv is not None
    assert loaded_inv.initial_finding is not None
    assert loaded_inv.initial_finding.id == finding.id
    assert len(loaded_inv.reports) == 1


def test_foreign_key_enforcement(db_session: Session) -> None:
    """Verify that foreign key constraints are enforced, rejecting invalid references."""
    # Inserting dataset with non-existent scenario_id must fail
    invalid_dataset = Dataset(
        id="ds_invalid",
        scenario_id="non_existent_scenario",
        name="orphaned.csv",
        file_path="orphan.csv",
        file_format="csv",
        file_size_bytes=100,
        record_count=1,
        column_count=1,
        schema_definition="[]",
    )
    db_session.add(invalid_dataset)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Inserting lineage edge with non-existent source_id must fail
    scenario = Scenario(id="sc_fk_test", name="FK Test")
    db_session.add(scenario)
    db_session.flush()

    node = LineageNode(
        id="node_valid",
        scenario_id=scenario.id,
        name="valid_node",
        node_type="METRIC",
    )
    db_session.add(node)
    db_session.flush()

    invalid_edge = LineageEdge(
        id="edge_invalid",
        scenario_id=scenario.id,
        source_id="non_existent_source",
        target_id=node.id,
    )
    db_session.add(invalid_edge)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cascade_delete_scenario(db_session: Session) -> None:
    """Verify that deleting a Scenario cascades to all 10 child tables."""
    now = datetime.now(UTC)
    scenario = Scenario(id="sc_cascade", name="Cascade Test")
    db_session.add(scenario)
    db_session.flush()

    dataset = Dataset(
        id="ds_cascade",
        scenario_id=scenario.id,
        name="data.csv",
        file_path="data.csv",
        file_format="csv",
        file_size_bytes=10,
        schema_definition="[]",
    )
    db_session.add(dataset)
    db_session.flush()

    rule = ValidationRule(
        id="rule_cascade",
        scenario_id=scenario.id,
        dataset_id=dataset.id,
        name="Rule",
        category="NULL_CHECK",
        severity="HIGH",
        parameters="{}",
    )
    val_run = ValidationRun(
        id="run_cascade",
        scenario_id=scenario.id,
        fixture_version="defective",
        status="PASSED",
        execution_duration_ms=10,
    )
    db_session.add_all([rule, val_run])
    db_session.flush()

    finding = ValidationFinding(
        id="find_cascade",
        run_id=val_run.id,
        rule_id=rule.id,
        dataset_id=dataset.id,
        rule_category="NULL_CHECK",
        severity="HIGH",
        status="PASSED",
        affected_fields="[]",
        message="Ok",
        evidence="{}",
        execution_duration_ms=5,
    )
    db_session.add(finding)

    node = LineageNode(
        id="node_cascade",
        scenario_id=scenario.id,
        name="Node",
        node_type="TRANSFORMATION",
    )
    db_session.add(node)
    db_session.flush()

    edge = LineageEdge(
        id="edge_cascade",
        scenario_id=scenario.id,
        source_id=node.id,
        target_id=node.id,
    )
    pipe = PipelineRun(
        id="pipe_cascade",
        scenario_id=scenario.id,
        pipeline_name="etl",
        execution_status="COMPLETED_SUCCESS",
        quality_health="HEALTHY",
        start_time=now,
        end_time=now,
        duration_ms=100,
    )
    fresh = FreshnessCheck(
        id="fresh_cascade",
        scenario_id=scenario.id,
        dataset_id=dataset.id,
        expected_partition_timestamp=now,
        sla_hours=12,
        status="FRESH",
    )
    inv = Investigation(
        id="inv_cascade",
        scenario_id=scenario.id,
        title="Inv",
        verified_facts="[]",
        hypotheses="[]",
        action_items="[]",
    )
    db_session.add_all([edge, pipe, fresh, inv])
    db_session.flush()

    rep = ReportArtifact(
        id="rep_cascade",
        investigation_id=inv.id,
        scenario_id=scenario.id,
        validation_run_id=val_run.id,
        format="json",
        file_path="report.json",
        sha256_hash="hash",
        file_size_bytes=100,
    )
    db_session.add(rep)
    db_session.commit()

    # Now delete the scenario
    db_session.delete(scenario)
    db_session.commit()

    # Verify that every entity associated with the scenario was deleted
    assert db_session.execute(select(Dataset)).scalars().all() == []
    assert db_session.execute(select(ValidationRule)).scalars().all() == []
    assert db_session.execute(select(ValidationRun)).scalars().all() == []
    assert db_session.execute(select(ValidationFinding)).scalars().all() == []
    assert db_session.execute(select(LineageNode)).scalars().all() == []
    assert db_session.execute(select(LineageEdge)).scalars().all() == []
    assert db_session.execute(select(PipelineRun)).scalars().all() == []
    assert db_session.execute(select(FreshnessCheck)).scalars().all() == []
    assert db_session.execute(select(Investigation)).scalars().all() == []
    assert db_session.execute(select(ReportArtifact)).scalars().all() == []


def test_cascade_delete_dataset(db_session: Session) -> None:
    """Verify deleting a Dataset cascades to rules/findings and SET NULL on lineage nodes."""
    now = datetime.now(UTC)
    scenario = Scenario(id="sc_ds_del", name="Dataset Delete Test")
    db_session.add(scenario)
    db_session.flush()

    dataset = Dataset(
        id="ds_to_delete",
        scenario_id=scenario.id,
        name="delete_me.csv",
        file_path="del.csv",
        file_format="csv",
        file_size_bytes=10,
        schema_definition="[]",
    )
    db_session.add(dataset)
    db_session.flush()

    rule = ValidationRule(
        id="rule_ds_del",
        scenario_id=scenario.id,
        dataset_id=dataset.id,
        name="Rule",
        category="NULL_CHECK",
        severity="LOW",
        parameters="{}",
    )
    val_run = ValidationRun(
        id="run_ds_del",
        scenario_id=scenario.id,
        fixture_version="defective",
        status="PASSED",
        execution_duration_ms=5,
    )
    db_session.add_all([rule, val_run])
    db_session.flush()

    finding = ValidationFinding(
        id="find_ds_del",
        run_id=val_run.id,
        rule_id=rule.id,
        dataset_id=dataset.id,
        rule_category="NULL_CHECK",
        severity="LOW",
        status="PASSED",
        affected_fields="[]",
        message="Ok",
        evidence="{}",
        execution_duration_ms=2,
    )
    fresh = FreshnessCheck(
        id="fresh_ds_del",
        scenario_id=scenario.id,
        dataset_id=dataset.id,
        expected_partition_timestamp=now,
        sla_hours=1,
        status="FRESH",
    )
    node = LineageNode(
        id="node_linked_to_ds",
        scenario_id=scenario.id,
        name="node_for_ds",
        node_type="SOURCE_DATASET",
        dataset_id=dataset.id,
    )
    db_session.add_all([finding, fresh, node])
    db_session.commit()

    # Delete the dataset
    db_session.delete(dataset)
    db_session.commit()

    # Rules, findings, and freshness checks targeting this dataset should be deleted
    assert db_session.get(ValidationRule, "rule_ds_del") is None
    assert db_session.get(ValidationFinding, "find_ds_del") is None
    assert db_session.get(FreshnessCheck, "fresh_ds_del") is None

    # Lineage node should still exist, but with dataset_id set to None (SET NULL)
    reloaded_node = db_session.get(LineageNode, "node_linked_to_ds")
    assert reloaded_node is not None
    assert reloaded_node.dataset_id is None


def test_initial_finding_set_null_on_investigation(db_session: Session) -> None:
    """Verify deleting a finding sets initial_finding_id on investigation to NULL."""
    scenario = Scenario(id="sc_inv_null", name="Inv Null Test")
    db_session.add(scenario)
    db_session.flush()

    dataset = Dataset(
        id="ds_inv_null",
        scenario_id=scenario.id,
        name="data.csv",
        file_path="data.csv",
        file_format="csv",
        file_size_bytes=10,
        schema_definition="[]",
    )
    rule = ValidationRule(
        id="rule_inv_null",
        scenario_id=scenario.id,
        dataset_id=dataset.id,
        name="Rule",
        category="NULL_CHECK",
        severity="LOW",
        parameters="{}",
    )
    val_run = ValidationRun(
        id="run_inv_null",
        scenario_id=scenario.id,
        fixture_version="defective",
        status="PASSED",
        execution_duration_ms=5,
    )
    db_session.add_all([dataset, rule, val_run])
    db_session.flush()

    finding = ValidationFinding(
        id="find_inv_null",
        run_id=val_run.id,
        rule_id=rule.id,
        dataset_id=dataset.id,
        rule_category="NULL_CHECK",
        severity="LOW",
        status="PASSED",
        affected_fields="[]",
        message="Ok",
        evidence="{}",
        execution_duration_ms=2,
    )
    db_session.add(finding)
    db_session.flush()

    investigation = Investigation(
        id="inv_find_test",
        scenario_id=scenario.id,
        title="Investigation Finding Test",
        initial_finding_id=finding.id,
        verified_facts="[]",
        hypotheses="[]",
        action_items="[]",
    )
    db_session.add(investigation)
    db_session.commit()

    # Delete the validation finding
    db_session.delete(finding)
    db_session.commit()

    reloaded_inv = db_session.get(Investigation, "inv_find_test")
    assert reloaded_inv is not None
    assert reloaded_inv.initial_finding_id is None


def test_cascade_delete_investigation(db_session: Session) -> None:
    """Verify deleting an investigation cascades to its report artifacts."""
    scenario = Scenario(id="sc_rep_casc", name="Rep Casc Test")
    val_run = ValidationRun(
        id="run_rep_casc",
        scenario_id=scenario.id,
        fixture_version="defective",
        status="PASSED",
        execution_duration_ms=5,
    )
    investigation = Investigation(
        id="inv_rep_casc",
        scenario_id=scenario.id,
        title="Inv",
        verified_facts="[]",
        hypotheses="[]",
        action_items="[]",
    )
    db_session.add_all([scenario, val_run, investigation])
    db_session.flush()

    report = ReportArtifact(
        id="rep_casc_item",
        investigation_id=investigation.id,
        scenario_id=scenario.id,
        validation_run_id=val_run.id,
        format="json",
        file_path="rep.json",
        sha256_hash="abc",
        file_size_bytes=50,
    )
    db_session.add(report)
    db_session.commit()

    # Delete investigation
    db_session.delete(investigation)
    db_session.commit()

    assert db_session.get(ReportArtifact, "rep_casc_item") is None


def test_init_db_creates_tables_and_wal_mode(tmp_path: Path) -> None:
    """Verify init_db initializes a file-based SQLite database with WAL mode and all 11 tables."""
    custom_db_path = tmp_path / "custom_dir" / "test_lux.db"
    custom_url = f"sqlite:///{custom_db_path.resolve()}"

    custom_engine = create_engine(
        custom_url,
        connect_args={"check_same_thread": False},
    )

    init_db(custom_engine)

    assert custom_db_path.exists()

    with custom_engine.connect() as conn:
        journal_mode = conn.execute(text("PRAGMA journal_mode")).scalar()
        assert str(journal_mode).lower() == "wal"

    inspector = inspect(custom_engine)
    created_tables = set(inspector.get_table_names())
    assert EXPECTED_TABLES.issubset(created_tables)
    custom_engine.dispose()
