# Lux REST API Contracts Specification

All API endpoints are prefixed with `/api/v1`. Responses are formatted in JSON, except for HTML report exports.

---

## 1. Standard Error Envelope

When an error occurs (HTTP 4xx or 5xx), the server returns a structured `ErrorResponse`:

```json
{
  "error": {
    "code": "DATASET_NOT_FOUND",
    "message": "Dataset with ID 'orders_unknown' does not exist in scenario 'monday_revenue_mystery'.",
    "details": {
      "scenario_id": "monday_revenue_mystery",
      "dataset_id": "orders_unknown"
    },
    "timestamp": "2026-10-20T22:30:00Z"
  }
}
```

---

## 2. Scenarios API

### 2.1 List Scenarios
- **Endpoint:** `GET /api/v1/scenarios`
- **Response (200 OK):**
```json
[
  {
    "id": "monday_revenue_mystery",
    "name": "Monday Revenue Mystery",
    "description": "Daily revenue metrics report unexpected spikes following a successful overnight pipeline run.",
    "category": "e-commerce",
    "is_bundled": true,
    "active_fixture_version": "defective",
    "dataset_count": 4,
    "rule_count": 12
  }
]
```

### 2.2 Get Scenario Details
- **Endpoint:** `GET /api/v1/scenarios/{id}`
- **Response (200 OK):** Detailed scenario object containing metadata, dataset list, and rule summaries.

### 2.3 Load Scenario
- **Endpoint:** `POST /api/v1/scenarios/{id}/load`
- **Request Body:**
```json
{
  "fixture_version": "defective"
}
```
*(Valid `fixture_version` values: `"defective"`, `"corrected"`)*
- **Response (200 OK):**
```json
{
  "scenario_id": "monday_revenue_mystery",
  "active_fixture_version": "defective",
  "loaded_datasets": ["orders", "order_items", "products", "inventory"],
  "rules_registered": 12,
  "lineage_nodes_loaded": 16,
  "message": "Scenario 'Monday Revenue Mystery' loaded successfully with defective fixtures."
}
```

---

## 3. Datasets API

### 3.1 List Datasets
- **Endpoint:** `GET /api/v1/datasets?scenario_id={scenario_id}`
- **Response (200 OK):**
```json
[
  {
    "id": "orders",
    "name": "orders.csv",
    "format": "csv",
    "file_size_bytes": 104857,
    "record_count": 1250,
    "column_count": 5
  }
]
```

### 3.2 Dataset Preview
- **Endpoint:** `GET /api/v1/datasets/{id}/preview?limit=50&offset=0`
- **Response (200 OK):**
```json
{
  "dataset_id": "orders",
  "total_records": 1250,
  "limit": 50,
  "offset": 0,
  "columns": ["order_id", "customer_id", "order_date", "order_status", "total_amount"],
  "rows": [
    {
      "order_id": "ORD-1001",
      "customer_id": "CUST-582",
      "order_date": "2026-10-19T08:14:22Z",
      "order_status": "COMPLETED",
      "total_amount": 149.50
    }
  ]
}
```

### 3.3 Upload Custom Dataset
- **Endpoint:** `POST /api/v1/datasets/upload`
- **Content-Type:** `multipart/form-data`
- **Form Parameters:**
  - `file`: CSV or JSON file (max 20MB).
  - `scenario_id`: Target scenario ID.
  - `dataset_name`: Name for the dataset.
- **Response (201 Created):**
```json
{
  "dataset_id": "upload_9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "name": "custom_transactions.csv",
  "format": "csv",
  "file_size_bytes": 204850,
  "record_count": 2100,
  "column_count": 6
}
```

---

## 4. Validations API

### 4.1 Execute Validation Run
- **Endpoint:** `POST /api/v1/validations/run`
- **Request Body:**
```json
{
  "scenario_id": "monday_revenue_mystery",
  "dataset_ids": ["orders", "order_items", "products", "inventory"]
}
```
- **Response (200 OK):**
```json
{
  "run_id": "val_run_18f6e2b4",
  "scenario_id": "monday_revenue_mystery",
  "fixture_version": "defective",
  "status": "FAILED",
  "total_checks": 12,
  "passed_checks": 8,
  "failed_checks": 4,
  "warning_checks": 0,
  "skipped_checks": 0,
  "error_checks": 0,
  "execution_duration_ms": 142,
  "executed_at": "2026-10-20T22:31:00Z"
}
```

### 4.2 List Validation Findings
- **Endpoint:** `GET /api/v1/validations/runs/{run_id}/findings?severity=CRITICAL&status=FAILED&limit=20&offset=0`
- **Response (200 OK):**
```json
{
  "run_id": "val_run_18f6e2b4",
  "total_findings": 4,
  "items": [
    {
      "id": "finding_001",
      "rule_id": "VAL-ORD-001",
      "rule_name": "Order ID Uniqueness Check",
      "rule_category": "UNIQUENESS",
      "severity": "CRITICAL",
      "status": "FAILED",
      "dataset_id": "orders",
      "affected_fields": ["order_id"],
      "affected_record_count": 15,
      "total_record_count": 1250,
      "message": "Found 15 duplicate order_id records in orders.csv.",
      "evidence": {
        "sample_duplicates": [
          {"order_id": "ORD-1042", "occurrences": 2, "row_indices": [42, 108]},
          {"order_id": "ORD-1088", "occurrences": 2, "row_indices": [88, 145]}
        ]
      },
      "execution_duration_ms": 14
    }
  ]
}
```

---

## 5. Lineage & Impact API

### 5.1 Get Lineage Graph
- **Endpoint:** `GET /api/v1/lineage?scenario_id=monday_revenue_mystery`
- **Response (200 OK):** Returns nodes and edges formatted for React Flow, with auto-calculated layout positions:
```json
{
  "scenario_id": "monday_revenue_mystery",
  "nodes": [
    {
      "id": "src_orders",
      "name": "orders.csv",
      "type": "SOURCE_DATASET",
      "dataset_id": "orders",
      "execution_status": "COMPLETED_SUCCESS",
      "quality_health": "CORRUPTED",
      "position": {"x": 50, "y": 100}
    },
    {
      "id": "tf_orders",
      "name": "transform_clean_orders",
      "type": "TRANSFORMATION",
      "execution_status": "COMPLETED_SUCCESS",
      "quality_health": "CORRUPTED",
      "position": {"x": 280, "y": 100}
    }
  ],
  "edges": [
    {
      "id": "e_orders_to_tf",
      "source": "src_orders",
      "target": "tf_orders"
    }
  ]
}
```

### 5.2 Trace Downstream Impact
- **Endpoint:** `POST /api/v1/impact/trace`
- **Request Body:**
```json
{
  "scenario_id": "monday_revenue_mystery",
  "target_type": "FINDING",
  "target_id": "finding_001"
}
```
*(Valid `target_type` values: `"FINDING"`, `"DATASET"`, `"NODE"`)*
- **Response (200 OK):**
```json
{
  "target_id": "finding_001",
  "root_dataset_id": "orders",
  "total_affected_assets": 4,
  "impact_summary": {
    "confirmed_failed": 1,
    "directly_affected": 1,
    "potentially_affected": 2
  },
  "affected_assets": [
    {
      "node_id": "src_orders",
      "name": "orders.csv",
      "type": "SOURCE_DATASET",
      "impact_status": "CONFIRMED_FAILED",
      "distance": 0,
      "dependency_path": ["src_orders"]
    },
    {
      "node_id": "dim_orders",
      "name": "dim_orders",
      "type": "DERIVED_DATASET",
      "impact_status": "DIRECTLY_AFFECTED",
      "distance": 2,
      "dependency_path": ["src_orders", "tf_orders", "dim_orders"]
    },
    {
      "node_id": "report_exec_dash",
      "name": "Report: Executive Monday Dashboard",
      "type": "REPORT",
      "impact_status": "POTENTIALLY_AFFECTED",
      "distance": 5,
      "dependency_path": ["src_orders", "tf_orders", "dim_orders", "tf_revenue", "agg_daily_revenue", "metric_revenue", "report_exec_dash"]
    }
  ]
}
```

---

## 6. Pipeline Observability API

### 6.1 List Pipeline Runs
- **Endpoint:** `GET /api/v1/pipelines/runs?scenario_id=monday_revenue_mystery&limit=10`
- **Response (200 OK):**
```json
[
  {
    "id": "pipe_run_20261020_0200",
    "scenario_id": "monday_revenue_mystery",
    "pipeline_name": "nightly_ecommerce_etl",
    "execution_status": "COMPLETED_SUCCESS",
    "quality_health": "CORRUPTED",
    "start_time": "2026-10-20T02:00:00Z",
    "end_time": "2026-10-20T02:08:14Z",
    "duration_ms": 494000,
    "records_ingested": 4670,
    "records_written": 4655,
    "error_message": null
  }
]
```

### 6.2 Get Data Freshness Status
- **Endpoint:** `GET /api/v1/pipelines/freshness?scenario_id=monday_revenue_mystery`
- **Response (200 OK):**
```json
[
  {
    "dataset_id": "orders",
    "dataset_name": "orders.csv",
    "sla_hours": 24,
    "expected_partition_timestamp": "2026-10-19T23:59:59Z",
    "observed_partition_timestamp": "2026-10-19T18:00:00Z",
    "status": "STALE",
    "hours_behind": 5.99
  }
]
```

---

## 7. Investigations & Reports API

### 7.1 Generate Incident Report
- **Endpoint:** `POST /api/v1/reports/generate`
- **Request Body:**
```json
{
  "scenario_id": "monday_revenue_mystery",
  "validation_run_id": "val_run_18f6e2b4",
  "title": "Investigation: Monday Morning Revenue Anomaly",
  "verified_facts": [
    "Overnight ETL pipeline succeeded at 02:08 UTC with exit code 0.",
    "15 duplicate order IDs detected in orders.csv.",
    "24 orphaned order items detected referencing invalid product IDs.",
    "Downstream Executive Dashboard is potentially compromised."
  ],
  "hypotheses": [
    "Upstream webhook duplicate delivery during Sunday night retry storm.",
    "Product catalog sync failed before order line items were ingested."
  ],
  "action_items": [
    "Deduplicate orders.csv using idempotent order UUID check.",
    "Backfill missing products.csv catalog rows.",
    "Re-execute daily revenue aggregation and verify metric recovery."
  ]
}
```
- **Response (201 Created):**
```json
{
  "report_id": "rep_9a8b7c6d",
  "investigation_id": "inv_12345678",
  "generated_at": "2026-10-20T22:32:00Z",
  "json_url": "/api/v1/reports/rep_9a8b7c6d/export?format=json",
  "html_url": "/api/v1/reports/rep_9a8b7c6d/export?format=html"
}
```

### 7.2 Download Report Artifact
- **Endpoint:** `GET /api/v1/reports/{id}/export?format=html`
- **Response (200 OK):**
  - For `format=json`: `application/json` payload containing full structured incident investigation.
  - For `format=html`: `text/html; charset=utf-8` standalone, sanitized, styled HTML document with embedded CSP headers.

---

## 8. Recovery Verification API

### 8.1 Verify Recovery
- **Endpoint:** `POST /api/v1/recovery/verify`
- **Request Body:**
```json
{
  "scenario_id": "monday_revenue_mystery"
}
```
- **Response (200 OK):**
```json
{
  "scenario_id": "monday_revenue_mystery",
  "comparison": {
    "previous_run": {
      "run_id": "val_run_18f6e2b4",
      "fixture_version": "defective",
      "failed_checks": 4,
      "quality_health": "CORRUPTED"
    },
    "current_run": {
      "run_id": "val_run_29a7f3c5",
      "fixture_version": "corrected",
      "failed_checks": 0,
      "quality_health": "HEALTHY"
    },
    "resolved_findings": [
      {"rule_id": "VAL-ORD-001", "rule_name": "Order ID Uniqueness Check", "status": "RESOLVED"},
      {"rule_id": "VAL-ORD-002", "rule_name": "Order Items Foreign Key Check", "status": "RESOLVED"},
      {"rule_id": "VAL-INV-001", "rule_name": "Inventory Non-Negative Check", "status": "RESOLVED"},
      {"rule_id": "VAL-FRESH-001", "rule_name": "Partition Freshness Check", "status": "RESOLVED"}
    ],
    "downstream_recovery_status": "ALL_ASSETS_HEALTHY"
  }
}
```

