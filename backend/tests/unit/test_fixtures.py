"""Unit tests for bundled scenario fixtures and metadata.

Validates that 'monday_revenue_mystery' fixtures satisfy all acceptance criteria:
1. Exact row counts: 1,250 orders, 3,420 order items, 250 products, 250 inventory records.
2. Defective fixtures contain exactly 15 duplicate orders, 24 orphaned items,
   8 negative inventory rows, and a 4-hour temporal gap.
3. Corrected fixtures contain 0 duplicates, 0 orphaned items, 0 negative inventory rows,
   and no temporal gap.
4. Lineage DAG contains 16 nodes, 14 edges, and is strictly acyclic.
5. All CSV and JSON files are UTF-8 encoded with LF line endings and no BOM.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import networkx as nx
import pytest

from app.core.config import settings
from app.services.ingestion.scenario_fixtures import (
    COUNT_INVENTORY,
    COUNT_ORDER_ITEMS,
    COUNT_ORDERS,
    COUNT_PRODUCTS,
    DEFECT_BROKEN_FOREIGN_KEYS,
    DEFECT_DUPLICATE_ORDERS,
    DEFECT_NEGATIVE_INVENTORY,
    SCENARIO_ID,
    generate_synthetic_data,
)


@pytest.fixture
def scenario_dir() -> Path:
    """Fixture providing the absolute path to the bundled scenario directory."""
    path = settings.scenarios_dir / SCENARIO_ID
    assert path.is_dir(), f"Scenario directory does not exist: {path}"
    return path


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file into a list of row dictionaries."""
    assert path.is_file(), f"File does not exist: {path}"
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def test_file_encodings_and_line_endings(scenario_dir: Path) -> None:
    """Verify all CSV and JSON files use UTF-8 without BOM and LF line endings."""
    for file_path in scenario_dir.rglob("*"):
        if file_path.is_file():
            raw_bytes = file_path.read_bytes()
            assert not raw_bytes.startswith(b"\xef\xbb\xbf"), f"BOM detected in {file_path.name}"
            assert b"\r\n" not in raw_bytes, f"CRLF line endings detected in {file_path.name}"


def test_scenario_metadata_structure_and_dag(scenario_dir: Path) -> None:
    """Verify scenario.json structure, dataset definitions, and 16-node lineage DAG."""
    scenario_path = scenario_dir / "scenario.json"
    with open(scenario_path, encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["id"] == SCENARIO_ID
    assert meta["name"] == "Monday Revenue Mystery"
    assert len(meta["datasets"]) == 4

    dataset_ids = {ds["id"] for ds in meta["datasets"]}
    assert dataset_ids == {"orders", "order_items", "products", "inventory"}

    # Verify Lineage DAG
    lineage = meta["lineage"]
    nodes = lineage["nodes"]
    edges = lineage["edges"]

    assert len(nodes) == 16, f"Expected 16 lineage nodes, got {len(nodes)}"
    assert len(edges) == 14, f"Expected 14 lineage edges, got {len(edges)}"

    node_ids = {n["id"] for n in nodes}
    assert len(node_ids) == 16, "All node IDs must be unique"

    # Build and test DAG in NetworkX
    dag = nx.DiGraph()
    for n in nodes:
        dag.add_node(n["id"], **n)
    for e in edges:
        assert e["source"] in node_ids, f"Edge source not in nodes: {e['source']}"
        assert e["target"] in node_ids, f"Edge target not in nodes: {e['target']}"
        dag.add_edge(e["source"], e["target"])

    assert nx.is_directed_acyclic_graph(dag), "Lineage graph must be strictly acyclic"

    # Verify key paths
    assert nx.has_path(dag, "src_orders", "report_exec_dash")
    assert nx.has_path(dag, "src_order_items", "report_exec_dash")
    assert nx.has_path(dag, "src_products", "report_exec_dash")
    assert nx.has_path(dag, "src_inventory", "report_stock_alert")


def test_validation_rules_metadata(scenario_dir: Path) -> None:
    """Verify rules.json contains required rules matching the defect catalog."""
    rules_path = scenario_dir / "rules.json"
    with open(rules_path, encoding="utf-8") as f:
        rules_data = json.load(f)

    assert rules_data["scenario_id"] == SCENARIO_ID
    rules = rules_data["rules"]
    assert len(rules) >= 4

    rule_ids = {r["id"] for r in rules}
    required_defect_rules = {"VAL-ORD-001", "VAL-ORD-002", "VAL-INV-001", "VAL-FRESH-001"}
    assert required_defect_rules.issubset(rule_ids), "Missing required defect rules"

    # Verify specific rule definitions
    rule_map = {r["id"]: r for r in rules}
    assert rule_map["VAL-ORD-001"]["category"] == "UNIQUENESS"
    assert rule_map["VAL-ORD-001"]["severity"] == "CRITICAL"
    assert rule_map["VAL-ORD-002"]["category"] == "REFERENTIAL_INTEGRITY"
    assert rule_map["VAL-ORD-002"]["severity"] == "HIGH"
    assert rule_map["VAL-INV-001"]["category"] == "VALUE_RANGE"
    assert rule_map["VAL-INV-001"]["severity"] == "HIGH"
    assert rule_map["VAL-FRESH-001"]["category"] == "FRESHNESS"
    assert rule_map["VAL-FRESH-001"]["severity"] == "MEDIUM"


def test_pipeline_history_metadata(scenario_dir: Path) -> None:
    """Verify pipeline_history.json reflects compute success vs quality corruption."""
    history_path = scenario_dir / "pipeline_history.json"
    with open(history_path, encoding="utf-8") as f:
        history = json.load(f)

    runs = history["pipeline_runs"]
    assert len(runs) >= 3

    # Latest run in defective state: compute SUCCESS, quality CORRUPTED
    latest_run = runs[-1]
    assert latest_run["execution_status"] == "COMPLETED_SUCCESS"
    assert latest_run["quality_health"] == "CORRUPTED"

    # Freshness check in defective state
    freshness = history["freshness_checks"]
    orders_freshness = next(fc for fc in freshness if fc["dataset_id"] == "orders")
    assert orders_freshness["status"] == "STALE"
    assert orders_freshness["hours_behind"] > 0

    # Corrected pipeline history
    cor_history_path = scenario_dir / "corrected" / "pipeline_history.json"
    assert cor_history_path.is_file()
    with open(cor_history_path, encoding="utf-8") as f:
        cor_history = json.load(f)

    cor_latest_run = cor_history["pipeline_runs"][-1]
    assert cor_latest_run["execution_status"] == "COMPLETED_SUCCESS"
    assert cor_latest_run["quality_health"] == "HEALTHY"

    cor_orders_freshness = next(
        fc for fc in cor_history["freshness_checks"] if fc["dataset_id"] == "orders"
    )
    assert cor_orders_freshness["status"] == "FRESH"
    assert cor_orders_freshness["hours_behind"] == 0.0


def test_fixture_row_counts_acceptance_criteria(scenario_dir: Path) -> None:
    """Verify exact row counts: 1,250 orders, 3,420 order items, 250 products, 250 inventory."""
    def_orders = _read_csv(scenario_dir / "defective" / "orders.csv")
    cor_orders = _read_csv(scenario_dir / "corrected" / "orders.csv")
    assert len(def_orders) == COUNT_ORDERS == 1250
    assert len(cor_orders) == COUNT_ORDERS == 1250

    def_items = _read_csv(scenario_dir / "defective" / "order_items.csv")
    cor_items = _read_csv(scenario_dir / "corrected" / "order_items.csv")
    assert len(def_items) == COUNT_ORDER_ITEMS == 3420
    assert len(cor_items) == COUNT_ORDER_ITEMS == 3420

    def_prods = _read_csv(scenario_dir / "defective" / "products.csv")
    cor_prods = _read_csv(scenario_dir / "corrected" / "products.csv")
    assert len(def_prods) == COUNT_PRODUCTS == 250
    assert len(cor_prods) == COUNT_PRODUCTS == 250

    def_inv = _read_csv(scenario_dir / "defective" / "inventory.csv")
    cor_inv = _read_csv(scenario_dir / "corrected" / "inventory.csv")
    assert len(def_inv) == COUNT_INVENTORY == 250
    assert len(cor_inv) == COUNT_INVENTORY == 250


def test_defective_fixtures_defects_acceptance_criteria(scenario_dir: Path) -> None:
    """Verify defective fixtures contain 15 duplicates, 24 broken FKs, 8 negative inventory."""
    # 1. Orders: exactly 15 duplicate order IDs
    orders = _read_csv(scenario_dir / "defective" / "orders.csv")
    order_counts = Counter(r["order_id"] for r in orders)
    duplicates = [oid for oid, cnt in order_counts.items() if cnt > 1]
    assert len(duplicates) == DEFECT_DUPLICATE_ORDERS == 15, (
        f"Expected 15 duplicate order IDs, found {len(duplicates)}"
    )

    duplicate_rows_count = len(orders) - len(order_counts)
    assert duplicate_rows_count == DEFECT_DUPLICATE_ORDERS == 15

    # Narrative revenue spike: verify duplicate orders sum to $142,000
    dup_set = set(duplicates)
    dup_rows = [r for r in orders if r["order_id"] in dup_set]
    # Each duplicate appears twice, so duplicate contribution is sum of one instance
    first_instances: dict[str, float] = {}
    for r in dup_rows:
        if r["order_id"] not in first_instances:
            first_instances[r["order_id"]] = float(r["total_amount"])
    revenue_spike = sum(first_instances.values())
    assert revenue_spike == pytest.approx(142000.00, 0.01), (
        f"Expected $142,000 revenue spike, got {revenue_spike}"
    )

    # Sunday temporal gap: 0 orders between 18:00 and 22:00 UTC
    gap_start = datetime(2026, 10, 18, 18, 0, 0, tzinfo=UTC)
    gap_end = datetime(2026, 10, 18, 22, 0, 0, tzinfo=UTC)
    gap_orders = [
        r
        for r in orders
        if gap_start <= datetime.fromisoformat(r["order_date"].replace("Z", "+00:00")) < gap_end
    ]
    assert len(gap_orders) == 0, f"Expected 0 orders in Sunday gap, found {len(gap_orders)}"

    # 2. Products & Order Items: exactly 24 orphaned items
    products = _read_csv(scenario_dir / "defective" / "products.csv")
    product_ids = {p["product_id"] for p in products}

    order_items = _read_csv(scenario_dir / "defective" / "order_items.csv")
    orphaned_items = [item for item in order_items if item["product_id"] not in product_ids]
    assert len(orphaned_items) == DEFECT_BROKEN_FOREIGN_KEYS == 24, (
        f"Expected 24 orphaned items, found {len(orphaned_items)}"
    )

    # 3. Inventory: exactly 8 negative quantity SKUs
    inventory = _read_csv(scenario_dir / "defective" / "inventory.csv")
    negative_inventory = [inv for inv in inventory if int(inv["quantity_on_hand"]) < 0]
    assert len(negative_inventory) == DEFECT_NEGATIVE_INVENTORY == 8, (
        f"Expected 8 negative inventory rows, found {len(negative_inventory)}"
    )


def test_corrected_fixtures_clean_acceptance_criteria(scenario_dir: Path) -> None:
    """Verify corrected fixtures contain 0 duplicates, 0 orphaned items, 0 negative inventory."""
    # 1. Orders: 0 duplicates and gap resolved
    orders = _read_csv(scenario_dir / "corrected" / "orders.csv")
    order_counts = Counter(r["order_id"] for r in orders)
    duplicates = [oid for oid, cnt in order_counts.items() if cnt > 1]
    assert len(duplicates) == 0, f"Expected 0 duplicate order IDs, found {len(duplicates)}"
    assert len(order_counts) == COUNT_ORDERS == 1250

    gap_start = datetime(2026, 10, 18, 18, 0, 0, tzinfo=UTC)
    gap_end = datetime(2026, 10, 18, 22, 0, 0, tzinfo=UTC)
    gap_orders = [
        r
        for r in orders
        if gap_start <= datetime.fromisoformat(r["order_date"].replace("Z", "+00:00")) < gap_end
    ]
    assert len(gap_orders) == DEFECT_DUPLICATE_ORDERS == 15, (
        f"Expected 15 orders filling the Sunday gap, found {len(gap_orders)}"
    )

    # 2. Order Items: 0 orphaned items
    products = _read_csv(scenario_dir / "corrected" / "products.csv")
    product_ids = {p["product_id"] for p in products}

    order_items = _read_csv(scenario_dir / "corrected" / "order_items.csv")
    orphaned_items = [item for item in order_items if item["product_id"] not in product_ids]
    assert len(orphaned_items) == 0, f"Expected 0 orphaned items, found {len(orphaned_items)}"

    # 3. Inventory: 0 negative quantity SKUs
    inventory = _read_csv(scenario_dir / "corrected" / "inventory.csv")
    negative_inventory = [inv for inv in inventory if int(inv["quantity_on_hand"]) < 0]
    assert len(negative_inventory) == 0, (
        f"Expected 0 negative inventory rows, found {len(negative_inventory)}"
    )


def test_synthetic_data_generator_determinism() -> None:
    """Verify that running the generator multiple times yields identical data structures."""
    run1 = generate_synthetic_data()
    run2 = generate_synthetic_data()

    assert run1["products"] == run2["products"]
    assert run1["inventory_defective"] == run2["inventory_defective"]
    assert run1["inventory_corrected"] == run2["inventory_corrected"]
    assert run1["orders_defective"] == run2["orders_defective"]
    assert run1["orders_corrected"] == run2["orders_corrected"]
    assert run1["order_items_defective"] == run2["order_items_defective"]
    assert run1["order_items_corrected"] == run2["order_items_corrected"]
