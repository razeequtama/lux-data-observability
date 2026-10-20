"""Deterministic synthetic fixture generator and scenario metadata definitions.

This module generates the bundled signature scenario: 'Monday Revenue Mystery'.
All synthetic fixtures, metadata, rules, and historical pipeline records are
generated deterministically using fixed seeds to ensure 100% reproducible test suites.
"""

from __future__ import annotations

import csv
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Scenario Identifier Constants
SCENARIO_ID = "monday_revenue_mystery"
SCENARIO_NAME = "Monday Revenue Mystery"
SCENARIO_DESCRIPTION = (
    "Daily revenue metrics report unexpected spikes following a successful overnight pipeline run."
)
SCENARIO_CATEGORY = "e-commerce"
SCENARIO_VERSION = "1.0.0"

# Target counts matching acceptance criteria
COUNT_ORDERS = 1250
COUNT_ORDER_ITEMS = 3420
COUNT_PRODUCTS = 250
COUNT_INVENTORY = 250

# Target defect counts
DEFECT_DUPLICATE_ORDERS = 15
DEFECT_BROKEN_FOREIGN_KEYS = 24
DEFECT_NEGATIVE_INVENTORY = 8


def get_scenario_metadata() -> dict[str, Any]:
    """Return the complete declarative scenario metadata specification."""
    return {
        "id": SCENARIO_ID,
        "name": SCENARIO_NAME,
        "description": SCENARIO_DESCRIPTION,
        "category": SCENARIO_CATEGORY,
        "version": SCENARIO_VERSION,
        "datasets": [
            {
                "id": "orders",
                "name": "orders.csv",
                "format": "csv",
                "defective_path": "defective/orders.csv",
                "corrected_path": "corrected/orders.csv",
                "expected_record_count": COUNT_ORDERS,
                "columns": [
                    {"name": "order_id", "type": "string", "nullable": False},
                    {"name": "customer_id", "type": "string", "nullable": False},
                    {"name": "order_date", "type": "timestamp", "nullable": False},
                    {"name": "order_status", "type": "string", "nullable": False},
                    {"name": "total_amount", "type": "float", "nullable": False},
                ],
            },
            {
                "id": "order_items",
                "name": "order_items.csv",
                "format": "csv",
                "defective_path": "defective/order_items.csv",
                "corrected_path": "corrected/order_items.csv",
                "expected_record_count": COUNT_ORDER_ITEMS,
                "columns": [
                    {"name": "item_id", "type": "string", "nullable": False},
                    {"name": "order_id", "type": "string", "nullable": False},
                    {"name": "product_id", "type": "string", "nullable": False},
                    {"name": "quantity", "type": "integer", "nullable": False},
                    {"name": "unit_price", "type": "float", "nullable": False},
                ],
            },
            {
                "id": "products",
                "name": "products.csv",
                "format": "csv",
                "defective_path": "defective/products.csv",
                "corrected_path": "corrected/products.csv",
                "expected_record_count": COUNT_PRODUCTS,
                "columns": [
                    {"name": "product_id", "type": "string", "nullable": False},
                    {"name": "sku", "type": "string", "nullable": False},
                    {"name": "category", "type": "string", "nullable": False},
                    {"name": "base_price", "type": "float", "nullable": False},
                ],
            },
            {
                "id": "inventory",
                "name": "inventory.csv",
                "format": "csv",
                "defective_path": "defective/inventory.csv",
                "corrected_path": "corrected/inventory.csv",
                "expected_record_count": COUNT_INVENTORY,
                "columns": [
                    {"name": "sku", "type": "string", "nullable": False},
                    {"name": "warehouse_id", "type": "string", "nullable": False},
                    {"name": "quantity_on_hand", "type": "integer", "nullable": False},
                    {"name": "last_updated", "type": "timestamp", "nullable": False},
                ],
            },
        ],
        "lineage": {
            "nodes": [
                {
                    "id": "src_orders",
                    "name": "orders.csv",
                    "type": "SOURCE_DATASET",
                    "dataset_id": "orders",
                },
                {
                    "id": "src_order_items",
                    "name": "order_items.csv",
                    "type": "SOURCE_DATASET",
                    "dataset_id": "order_items",
                },
                {
                    "id": "src_products",
                    "name": "products.csv",
                    "type": "SOURCE_DATASET",
                    "dataset_id": "products",
                },
                {
                    "id": "src_inventory",
                    "name": "inventory.csv",
                    "type": "SOURCE_DATASET",
                    "dataset_id": "inventory",
                },
                {
                    "id": "tf_orders",
                    "name": "transform_clean_orders",
                    "type": "TRANSFORMATION",
                    "metadata": {"engine": "SQL"},
                },
                {
                    "id": "tf_items",
                    "name": "transform_order_line_items",
                    "type": "TRANSFORMATION",
                    "metadata": {"engine": "SQL"},
                },
                {
                    "id": "tf_inventory",
                    "name": "transform_inventory_snapshot",
                    "type": "TRANSFORMATION",
                    "metadata": {"engine": "Python"},
                },
                {
                    "id": "tf_revenue",
                    "name": "aggregate_daily_revenue",
                    "type": "TRANSFORMATION",
                    "metadata": {"engine": "SQL"},
                },
                {"id": "dim_orders", "name": "dim_orders", "type": "DERIVED_DATASET"},
                {"id": "fct_order_items", "name": "fct_order_items", "type": "DERIVED_DATASET"},
                {"id": "dim_inventory", "name": "dim_inventory", "type": "DERIVED_DATASET"},
                {"id": "agg_daily_revenue", "name": "agg_daily_revenue", "type": "DERIVED_DATASET"},
                {"id": "metric_revenue", "name": "Metric: Total Daily Revenue", "type": "METRIC"},
                {
                    "id": "metric_inventory",
                    "name": "Metric: Inventory Health Ratio",
                    "type": "METRIC",
                },
                {
                    "id": "report_exec_dash",
                    "name": "Report: Executive Monday Dashboard",
                    "type": "REPORT",
                },
                {
                    "id": "report_stock_alert",
                    "name": "Report: Warehouse Stock Alert",
                    "type": "REPORT",
                },
            ],
            "edges": [
                {"source": "src_orders", "target": "tf_orders"},
                {"source": "tf_orders", "target": "dim_orders"},
                {"source": "src_order_items", "target": "tf_items"},
                {"source": "src_products", "target": "tf_items"},
                {"source": "tf_items", "target": "fct_order_items"},
                {"source": "src_inventory", "target": "tf_inventory"},
                {"source": "tf_inventory", "target": "dim_inventory"},
                {"source": "dim_orders", "target": "tf_revenue"},
                {"source": "fct_order_items", "target": "tf_revenue"},
                {"source": "tf_revenue", "target": "agg_daily_revenue"},
                {"source": "agg_daily_revenue", "target": "metric_revenue"},
                {"source": "metric_revenue", "target": "report_exec_dash"},
                {"source": "dim_inventory", "target": "metric_inventory"},
                {"source": "metric_inventory", "target": "report_stock_alert"},
            ],
        },
    }


def get_rules_metadata() -> dict[str, Any]:
    """Return the declarative validation rules matching the scenario defect catalog."""
    return {
        "scenario_id": SCENARIO_ID,
        "rules": [
            {
                "id": "VAL-ORD-001",
                "dataset_id": "orders",
                "name": "Order ID Uniqueness Check",
                "category": "UNIQUENESS",
                "severity": "CRITICAL",
                "parameters": {"column": "order_id"},
                "description": (
                    "Ensures all order IDs in orders.csv are unique and no duplicates exist."
                ),
                "is_active": True,
            },
            {
                "id": "VAL-ORD-002",
                "dataset_id": "order_items",
                "name": "Order Items Foreign Key Check",
                "category": "REFERENTIAL_INTEGRITY",
                "severity": "HIGH",
                "parameters": {
                    "column": "product_id",
                    "parent_dataset": "products",
                    "parent_column": "product_id",
                },
                "description": (
                    "Ensures all product_id references in order_items.csv exist in products.csv."
                ),
                "is_active": True,
            },
            {
                "id": "VAL-INV-001",
                "dataset_id": "inventory",
                "name": "Inventory Non-Negative Check",
                "category": "VALUE_RANGE",
                "severity": "HIGH",
                "parameters": {"column": "quantity_on_hand", "min_value": 0},
                "description": "Ensures inventory quantity on hand is never negative.",
                "is_active": True,
            },
            {
                "id": "VAL-FRESH-001",
                "dataset_id": "orders",
                "name": "Partition Freshness Check",
                "category": "FRESHNESS",
                "severity": "MEDIUM",
                "parameters": {
                    "column": "order_date",
                    "sla_hours": 24,
                    "max_gap_hours": 4,
                },
                "description": (
                    "Detects missing transaction windows or ingestion delays exceeding "
                    "SLA thresholds."
                ),
                "is_active": True,
            },
            {
                "id": "VAL-ORD-003",
                "dataset_id": "orders",
                "name": "Orders Mandatory Fields Check",
                "category": "NULL_CHECK",
                "severity": "CRITICAL",
                "parameters": {
                    "columns": ["order_id", "customer_id", "order_date", "total_amount"]
                },
                "description": (
                    "Verifies that essential order header fields contain no null or empty values."
                ),
                "is_active": True,
            },
            {
                "id": "VAL-PRD-001",
                "dataset_id": "products",
                "name": "Product ID Uniqueness Check",
                "category": "UNIQUENESS",
                "severity": "CRITICAL",
                "parameters": {"column": "product_id"},
                "description": "Ensures product catalog primary keys are unique.",
                "is_active": True,
            },
            {
                "id": "VAL-PRD-002",
                "dataset_id": "products",
                "name": "Product Base Price Positive Check",
                "category": "VALUE_RANGE",
                "severity": "HIGH",
                "parameters": {"column": "base_price", "min_value": 0.01},
                "description": "Ensures base price of products is greater than zero.",
                "is_active": True,
            },
            {
                "id": "VAL-INV-002",
                "dataset_id": "inventory",
                "name": "Inventory SKU Uniqueness Check",
                "category": "UNIQUENESS",
                "severity": "CRITICAL",
                "parameters": {"column": "sku"},
                "description": "Ensures each SKU has a single inventory record per warehouse.",
                "is_active": True,
            },
        ],
    }


def get_pipeline_history_metadata(is_corrected: bool = False) -> dict[str, Any]:
    """Return pipeline execution history logs and freshness SLA specifications."""
    latest_quality_health = "HEALTHY" if is_corrected else "CORRUPTED"
    orders_freshness_status = "FRESH" if is_corrected else "STALE"
    orders_observed_timestamp = "2026-10-19T23:55:00Z" if is_corrected else "2026-10-19T18:00:00Z"
    orders_hours_behind = 0.0 if is_corrected else 5.99

    return {
        "scenario_id": SCENARIO_ID,
        "pipeline_runs": [
            {
                "id": "pipe_run_20261018_0200",
                "scenario_id": SCENARIO_ID,
                "pipeline_name": "nightly_ecommerce_etl",
                "execution_status": "COMPLETED_SUCCESS",
                "quality_health": "HEALTHY",
                "start_time": "2026-10-18T02:00:00Z",
                "end_time": "2026-10-18T02:07:45Z",
                "duration_ms": 465000,
                "records_ingested": 4500,
                "records_written": 4500,
                "error_message": None,
                "run_log": [
                    {
                        "step": "extract_sources",
                        "status": "SUCCESS",
                        "records": 4500,
                        "duration_ms": 110000,
                    },
                    {
                        "step": "transform_clean_orders",
                        "status": "SUCCESS",
                        "records": 1200,
                        "duration_ms": 95000,
                    },
                    {
                        "step": "transform_order_line_items",
                        "status": "SUCCESS",
                        "records": 3300,
                        "duration_ms": 140000,
                    },
                    {
                        "step": "aggregate_daily_revenue",
                        "status": "SUCCESS",
                        "records": 1,
                        "duration_ms": 120000,
                    },
                ],
            },
            {
                "id": "pipe_run_20261019_0200",
                "scenario_id": SCENARIO_ID,
                "pipeline_name": "nightly_ecommerce_etl",
                "execution_status": "COMPLETED_SUCCESS",
                "quality_health": "HEALTHY",
                "start_time": "2026-10-19T02:00:00Z",
                "end_time": "2026-10-19T02:08:02Z",
                "duration_ms": 482000,
                "records_ingested": 4600,
                "records_written": 4600,
                "error_message": None,
                "run_log": [
                    {
                        "step": "extract_sources",
                        "status": "SUCCESS",
                        "records": 4600,
                        "duration_ms": 115000,
                    },
                    {
                        "step": "transform_clean_orders",
                        "status": "SUCCESS",
                        "records": 1220,
                        "duration_ms": 98000,
                    },
                    {
                        "step": "transform_order_line_items",
                        "status": "SUCCESS",
                        "records": 3380,
                        "duration_ms": 145000,
                    },
                    {
                        "step": "aggregate_daily_revenue",
                        "status": "SUCCESS",
                        "records": 1,
                        "duration_ms": 124000,
                    },
                ],
            },
            {
                "id": "pipe_run_20261020_0200",
                "scenario_id": SCENARIO_ID,
                "pipeline_name": "nightly_ecommerce_etl",
                "execution_status": "COMPLETED_SUCCESS",
                "quality_health": latest_quality_health,
                "start_time": "2026-10-20T02:00:00Z",
                "end_time": "2026-10-20T02:08:14Z",
                "duration_ms": 494000,
                "records_ingested": 4670,
                "records_written": 4670 if is_corrected else 4655,
                "error_message": None,
                "run_log": [
                    {
                        "step": "extract_sources",
                        "status": "SUCCESS",
                        "records": 4670,
                        "duration_ms": 120000,
                    },
                    {
                        "step": "transform_clean_orders",
                        "status": "SUCCESS",
                        "records": COUNT_ORDERS,
                        "duration_ms": 102000,
                    },
                    {
                        "step": "transform_order_line_items",
                        "status": "SUCCESS",
                        "records": COUNT_ORDER_ITEMS,
                        "duration_ms": 147000,
                    },
                    {
                        "step": "aggregate_daily_revenue",
                        "status": "SUCCESS",
                        "records": 1,
                        "duration_ms": 125000,
                    },
                ],
            },
        ],
        "freshness_checks": [
            {
                "id": "fresh_orders_20261020",
                "scenario_id": SCENARIO_ID,
                "dataset_id": "orders",
                "dataset_name": "orders.csv",
                "expected_partition_timestamp": "2026-10-19T23:59:59Z",
                "observed_partition_timestamp": orders_observed_timestamp,
                "sla_hours": 24,
                "status": orders_freshness_status,
                "hours_behind": orders_hours_behind,
                "checked_at": "2026-10-20T02:10:00Z",
            },
            {
                "id": "fresh_inventory_20261020",
                "scenario_id": SCENARIO_ID,
                "dataset_id": "inventory",
                "dataset_name": "inventory.csv",
                "expected_partition_timestamp": "2026-10-20T01:00:00Z",
                "observed_partition_timestamp": "2026-10-20T01:30:00Z",
                "sla_hours": 6,
                "status": "FRESH",
                "hours_behind": 0.0,
                "checked_at": "2026-10-20T02:10:00Z",
            },
        ],
    }


def generate_synthetic_data() -> dict[str, Any]:
    """Generate deterministic data rows for defective and corrected fixtures.

    Returns:
        dict containing:
            - 'products': list of product dicts (250)
            - 'inventory_defective': list of inventory dicts (250, 8 negative)
            - 'inventory_corrected': list of inventory dicts (250, 0 negative)
            - 'orders_defective': list of order dicts (1250, 15 duplicate IDs, Sunday gap)
            - 'orders_corrected': list of order dicts (1250, 0 duplicates, no gap)
            - 'order_items_defective': list of item dicts (3420, 24 broken FKs)
            - 'order_items_corrected': list of item dicts (3420, 0 broken FKs)
    """
    rng = random.Random(42)

    # 1. Products (250 rows)
    categories = [
        "Electronics",
        "Apparel",
        "Home & Kitchen",
        "Beauty & Personal Care",
        "Sports & Outdoors",
    ]
    products: list[dict[str, Any]] = []
    product_price_map: dict[str, float] = {}

    for i in range(1, COUNT_PRODUCTS + 1):
        pid = f"PRD-{i:04d}"
        sku = f"SKU-{i:04d}"
        cat = categories[(i - 1) % len(categories)]
        # Deterministic base prices between $12.50 and $249.99
        base_price = round(12.50 + ((i * 17) % 237) + ((i % 10) * 0.49), 2)
        products.append(
            {
                "product_id": pid,
                "sku": sku,
                "category": cat,
                "base_price": base_price,
            }
        )
        product_price_map[pid] = base_price

    # 2. Inventory (250 rows)
    warehouses = ["WH-NORTH", "WH-SOUTH", "WH-EAST", "WH-WEST"]
    inventory_defective: list[dict[str, Any]] = []
    inventory_corrected: list[dict[str, Any]] = []

    # 8 deterministic SKUs with negative inventory in defective
    negative_sku_indices = {12, 34, 56, 78, 90, 112, 145, 180}
    negative_values = {
        12: -12,
        34: -5,
        56: -18,
        78: -3,
        90: -8,
        112: -15,
        145: -20,
        180: -7,
    }
    corrected_values = {
        12: 12,
        34: 25,
        56: 18,
        78: 30,
        90: 42,
        112: 15,
        145: 50,
        180: 35,
    }

    inv_timestamp = "2026-10-20T01:30:00Z"
    for i in range(1, COUNT_PRODUCTS + 1):
        sku = f"SKU-{i:04d}"
        wh = warehouses[(i - 1) % len(warehouses)]
        normal_qty = 20 + ((i * 31) % 450)

        if i in negative_sku_indices:
            qty_defective = negative_values[i]
            qty_corrected = corrected_values[i]
        else:
            qty_defective = normal_qty
            qty_corrected = normal_qty

        inventory_defective.append(
            {
                "sku": sku,
                "warehouse_id": wh,
                "quantity_on_hand": qty_defective,
                "last_updated": inv_timestamp,
            }
        )
        inventory_corrected.append(
            {
                "sku": sku,
                "warehouse_id": wh,
                "quantity_on_hand": qty_corrected,
                "last_updated": inv_timestamp,
            }
        )

    # 3. Orders (1250 rows)
    # Date window: Sunday 2026-10-18 00:00:00 UTC to Monday 2026-10-19 23:59:59 UTC
    start_dt = datetime(2026, 10, 18, 0, 0, 0, tzinfo=UTC)
    # Missing window in defective: Sunday 18:00 to 22:00 UTC
    gap_start = datetime(2026, 10, 18, 18, 0, 0, tzinfo=UTC)
    gap_end = datetime(2026, 10, 18, 22, 0, 0, tzinfo=UTC)

    # We need 1235 unique orders for defective, plus 15 duplicate occurrences = 1250 total rows
    # In corrected, we have 1250 unique orders (0 duplicates)
    statuses = ["completed", "shipped", "delivered"]
    unique_orders_base: list[dict[str, Any]] = []

    # Generate 1235 unique orders that respect the Sunday gap
    current_time = start_dt
    order_idx = 1
    while len(unique_orders_base) < (COUNT_ORDERS - DEFECT_DUPLICATE_ORDERS):
        # Step forward in time (averaging ~2 minutes per order across 48 hours)
        offset_seconds = rng.randint(90, 180)
        candidate_time = current_time + timedelta(seconds=offset_seconds)
        if candidate_time > datetime(2026, 10, 19, 23, 50, 0, tzinfo=UTC):
            candidate_time = start_dt + timedelta(seconds=rng.randint(0, 48 * 3600 - 1))

        # In defective base, skip Sunday 18:00 - 22:00 UTC
        if gap_start <= candidate_time < gap_end:
            # Shift to Monday or post-gap
            candidate_time = gap_end + timedelta(minutes=rng.randint(5, 60))

        current_time = candidate_time
        oid = f"ORD-{order_idx:04d}"
        cid = f"CUST-{(order_idx * 37) % 500 + 1:04d}"
        status = statuses[(order_idx - 1) % len(statuses)]
        amount = round(25.0 + ((order_idx * 13) % 275) + 0.99, 2)

        unique_orders_base.append(
            {
                "order_id": oid,
                "customer_id": cid,
                "order_date": candidate_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "order_status": status,
                "total_amount": amount,
            }
        )
        order_idx += 1

    # 15 duplicate orders in defective:
    # 10 orders of $9,500.00 and 5 orders of $9,400.00 = $95,000 + $47,000 = $142,000 total spike!
    duplicate_indices = [15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225]
    spike_amounts = [9500.00] * 10 + [9400.00] * 5

    # Assign wholesale amounts to the 15 selected orders in unique_orders_base
    for idx_pos, base_idx in enumerate(duplicate_indices):
        unique_orders_base[base_idx - 1]["total_amount"] = spike_amounts[idx_pos]

    # Build defective orders: 1235 unique + 15 duplicate records = 1250
    orders_defective: list[dict[str, Any]] = list(unique_orders_base)
    for base_idx in duplicate_indices:
        # Duplicate record with exact same order_id, customer, date, status, and amount
        duplicate_record = dict(unique_orders_base[base_idx - 1])
        orders_defective.append(duplicate_record)

    # Build corrected orders:
    # The 1235 unique orders remain, plus 15 brand new unique orders (ORD-1236 to ORD-1250)
    # placed squarely within the Sunday gap (18:00 to 22:00) with normal amounts,
    # and the original 15 orders have normal amounts instead of $142,000 spike!
    orders_corrected: list[dict[str, Any]] = []
    for item in unique_orders_base:
        clean_item = dict(item)
        orders_corrected.append(clean_item)

    # Revert the 15 wholesale spike amounts to regular retail amounts in corrected
    for idx_pos, base_idx in enumerate(duplicate_indices):
        orders_corrected[base_idx - 1]["total_amount"] = round(45.0 + (base_idx % 120) + 0.99, 2)

    # Add 15 new unique orders into the Sunday gap window (18:00 - 22:00)
    gap_duration_seconds = int((gap_end - gap_start).total_seconds())
    for extra_i in range(DEFECT_DUPLICATE_ORDERS):
        new_oid = f"ORD-{COUNT_ORDERS - DEFECT_DUPLICATE_ORDERS + extra_i + 1:04d}"
        new_cid = f"CUST-{(extra_i * 43) % 500 + 1:04d}"
        gap_offset = int((extra_i + 1) * (gap_duration_seconds / (DEFECT_DUPLICATE_ORDERS + 1)))
        gap_time = gap_start + timedelta(seconds=gap_offset)
        orders_corrected.append(
            {
                "order_id": new_oid,
                "customer_id": new_cid,
                "order_date": gap_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "order_status": "completed",
                "total_amount": round(50.0 + (extra_i * 12.5), 2),
            }
        )

    # Sort corrected orders by order_id to keep clean sequence
    orders_corrected.sort(key=lambda x: x["order_id"])

    # 4. Order Items (3420 rows)
    # Distribute 3420 items across the unique orders (ORD-0001 to ORD-1235)
    # So every order in order_items exists in both defective and corrected orders!
    order_items_defective: list[dict[str, Any]] = []
    order_items_corrected: list[dict[str, Any]] = []

    # Exactly 24 broken foreign keys: item_idx 100, 200, 300, ..., 2400
    broken_item_indices = {i * 100 for i in range(1, DEFECT_BROKEN_FOREIGN_KEYS + 1)}
    broken_product_ids = {
        i * 100: f"PRD-{9000 + i:04d}" for i in range(1, DEFECT_BROKEN_FOREIGN_KEYS + 1)
    }

    num_unique_orders = COUNT_ORDERS - DEFECT_DUPLICATE_ORDERS  # 1235
    for item_idx in range(1, COUNT_ORDER_ITEMS + 1):
        item_id = f"ITM-{item_idx:04d}"
        # Map deterministically to an order_id between ORD-0001 and ORD-1235
        parent_order_num = ((item_idx * 7) % num_unique_orders) + 1
        order_id = f"ORD-{parent_order_num:04d}"

        # Valid product between PRD-0001 and PRD-0250
        valid_product_num = ((item_idx * 11) % COUNT_PRODUCTS) + 1
        valid_product_id = f"PRD-{valid_product_num:04d}"
        qty = ((item_idx * 3) % 5) + 1
        price = product_price_map.get(valid_product_id, 29.99)

        if item_idx in broken_item_indices:
            defective_pid = broken_product_ids[item_idx]
        else:
            defective_pid = valid_product_id

        order_items_defective.append(
            {
                "item_id": item_id,
                "order_id": order_id,
                "product_id": defective_pid,
                "quantity": qty,
                "unit_price": price,
            }
        )

        order_items_corrected.append(
            {
                "item_id": item_id,
                "order_id": order_id,
                "product_id": valid_product_id,
                "quantity": qty,
                "unit_price": price,
            }
        )

    return {
        "products": products,
        "inventory_defective": inventory_defective,
        "inventory_corrected": inventory_corrected,
        "orders_defective": orders_defective,
        "orders_corrected": orders_corrected,
        "order_items_defective": order_items_defective,
        "order_items_corrected": order_items_corrected,
    }


def write_csv_file(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    """Write list of dicts to CSV file with UTF-8 encoding and LF line endings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json_file(path: Path, data: Any) -> None:
    """Write data to JSON file with UTF-8 encoding, LF line endings, and 2-space indentation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    with open(path, mode="w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def generate_scenario_files(base_dir: Path) -> dict[str, Path]:
    """Generate all scenario metadata, rules, history, and CSV fixtures.

    Args:
        base_dir: Root scenarios directory (e.g., data/scenarios/monday_revenue_mystery).

    Returns:
        dict of written file keys and their Path objects.
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    defective_dir = base_dir / "defective"
    corrected_dir = base_dir / "corrected"
    defective_dir.mkdir(parents=True, exist_ok=True)
    corrected_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write root metadata files
    scenario_json_path = base_dir / "scenario.json"
    rules_json_path = base_dir / "rules.json"
    history_json_path = base_dir / "pipeline_history.json"
    corrected_history_json_path = corrected_dir / "pipeline_history.json"

    write_json_file(scenario_json_path, get_scenario_metadata())
    write_json_file(rules_json_path, get_rules_metadata())
    write_json_file(history_json_path, get_pipeline_history_metadata(is_corrected=False))
    write_json_file(corrected_history_json_path, get_pipeline_history_metadata(is_corrected=True))

    # 2. Generate synthetic data
    data = generate_synthetic_data()

    # 3. Write CSV fixtures
    # Products (both defective and corrected are identical)
    product_fields = ["product_id", "sku", "category", "base_price"]
    def_prod_path = defective_dir / "products.csv"
    cor_prod_path = corrected_dir / "products.csv"
    write_csv_file(def_prod_path, data["products"], product_fields)
    write_csv_file(cor_prod_path, data["products"], product_fields)

    # Inventory
    inv_fields = ["sku", "warehouse_id", "quantity_on_hand", "last_updated"]
    def_inv_path = defective_dir / "inventory.csv"
    cor_inv_path = corrected_dir / "inventory.csv"
    write_csv_file(def_inv_path, data["inventory_defective"], inv_fields)
    write_csv_file(cor_inv_path, data["inventory_corrected"], inv_fields)

    # Orders
    orders_fields = ["order_id", "customer_id", "order_date", "order_status", "total_amount"]
    def_orders_path = defective_dir / "orders.csv"
    cor_orders_path = corrected_dir / "orders.csv"
    write_csv_file(def_orders_path, data["orders_defective"], orders_fields)
    write_csv_file(cor_orders_path, data["orders_corrected"], orders_fields)

    # Order Items
    items_fields = ["item_id", "order_id", "product_id", "quantity", "unit_price"]
    def_items_path = defective_dir / "order_items.csv"
    cor_items_path = corrected_dir / "order_items.csv"
    write_csv_file(def_items_path, data["order_items_defective"], items_fields)
    write_csv_file(cor_items_path, data["order_items_corrected"], items_fields)

    return {
        "scenario_json": scenario_json_path,
        "rules_json": rules_json_path,
        "pipeline_history_json": history_json_path,
        "corrected_pipeline_history_json": corrected_history_json_path,
        "defective_products": def_prod_path,
        "corrected_products": cor_prod_path,
        "defective_inventory": def_inv_path,
        "corrected_inventory": cor_inv_path,
        "defective_orders": def_orders_path,
        "corrected_orders": cor_orders_path,
        "defective_order_items": def_items_path,
        "corrected_order_items": cor_items_path,
    }


if __name__ == "__main__":
    # When run directly, generate fixtures into default data/scenarios directory
    from app.core.config import settings

    target_scenario_dir = settings.scenarios_dir / SCENARIO_ID
    print(f"Generating fixtures in: {target_scenario_dir}")
    files = generate_scenario_files(target_scenario_dir)
    print(f"Successfully generated {len(files)} scenario files.")
