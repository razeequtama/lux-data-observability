# Lux Implementation Progress Tracker

This document is the single source of truth for implementation tracking across engineering sessions. All coding agents must update this document upon completing a task.

---

## 1. Milestone Status Overview

| Milestone | Description | Tasks | Status |
|---|---|---|---|
| **M0** | Core Foundation, Tooling & Scaffolding | `T01`, `T02` | `COMPLETED` |
| **M1** | Persistence, Scenario Data Foundation & Ingestion Engine | `T03`, `T04`, `T05` | `COMPLETED` |
| **M2** | Deterministic Data Quality Validation Engine | `T06`, `T07`, `T08` | `COMPLETED` |
| **M3** | Lineage DAG Domain Engine & Graph Integrity Validator | `T09`, `T10`, `T11` | `COMPLETED` |
| **M4** | Pipeline Observability & Run History | `T12`, `T13` | `NOT_STARTED` |
| **M5** | Incident Investigation & Safe Report Generation | `T14`, `T15` | `NOT_STARTED` |
| **M6** | Frontend "Trace the Failure" Interactive UI | `T16`, `T17`, `T18`, `T19`, `T20` | `NOT_STARTED` |
| **M7** | Recovery Verification & End-to-End Acceptance | `T21`, `T22`, `T23` | `NOT_STARTED` |
| **M8** | Containerization & Operational Polish | `T24` | `NOT_STARTED` |

---

## 2. Detailed Task Tracking

| Task ID | Task Title | Prerequisites | Status | Verification Summary |
|---|---|---|---|---|
| `T01` | Backend Scaffolding, Tooling & Base Configuration | None | `COMPLETED` | `pytest` 5 passed; `ruff` and `mypy` 0 errors; `/health` returns 200 OK |
| `T02` | Frontend Scaffolding, Tooling & Lux Purple Tokens | None | `COMPLETED` | `vitest` 6 passed; `tsc` & `eslint` 0 errors; production build verified |
| `T03` | Relational Database Schema & SQLite Persistence Engine | `T01` | `COMPLETED` | `pytest` 14 passed (9 db integration); `ruff` & `mypy` 0 errors; WAL mode, all 11 tables, indices, and cascades verified |
| `T04` | Bundled Signature Fixtures & Scenario Metadata Definition | None | `COMPLETED` | `pytest tests/unit/test_fixtures.py` 8 passed; 1,250 orders, 3,420 items, 250 prods, 250 inv; 15 dups, 24 orphaned, 8 neg inv, 1 temporal gap verified |
| `T05` | Dataset Ingestion, Scenario Loader & Upload Security Service | `T01`, `T03`, `T04` | `COMPLETED` | `pytest tests/integration/test_ingestion_api.py` 14 passed; `pytest` 43 passed; `ruff` and `mypy` 0 errors; load scenario (200), preview, 20MB limit (413), and path traversal rejection (400) verified |
| `T06` | Validation Rule Framework & Core Rule Evaluators | `T01`, `T03` | `COMPLETED` | `pytest tests/unit/test_rules_core.py` 38 passed; full `pytest` 81 passed; `ruff` and `mypy` 0 errors; detected 15 duplicates in orders.csv and 8 negative inventory SKUs in inventory.csv |
| `T07` | Relational, Temporal & Schema Rule Evaluators | `T06` | `COMPLETED` | `pytest tests/unit/test_rules_relational.py` 25 passed; full `pytest` 106 passed; `ruff` and `mypy` 0 errors; detected 24 orphaned items in order_items.csv and Sunday 4.47h gap in orders.csv; clean recovery verified |
| `T08` | Validation Runner Service, Persistence & Structured Findings API | `T03`, `T05`, `T06`, `T07` | `COMPLETED` | `pytest tests/integration/test_validations_api.py` 14 passed; full `pytest` 120 passed; `ruff` and `mypy` 0 errors; exactly 4 failed checks detected on defective fixtures; structured sample keys & capping verified |
| `T09` | Lineage DAG Domain Engine & Graph Integrity Validator | `T01`, `T03` | `COMPLETED` | `pytest tests/unit/test_lineage_graph.py` 22 passed; full `pytest` 142 passed; `ruff` & `mypy` 0 errors; rejected cyclic graphs with `CyclicDependencyError`; loaded 16-node 14-edge scenario cleanly; verified upstream ancestors of `report_exec_dash` include `orders` and `order_items` |
| `T10` | Downstream Impact Analysis Engine & Blast Radius Classifier | `T08`, `T09` | `COMPLETED` | `pytest tests/unit/test_impact_analysis.py` 13 passed; full `pytest` 155 passed; `ruff` & `mypy` 0 errors; orders.csv blast radius correctly classifies `dim_orders` as `DIRECTLY_AFFECTED` and `agg_daily_revenue`, `metric_revenue`, `report_exec_dash` as `POTENTIALLY_AFFECTED` |
| `T11` | Lineage & Impact REST API Endpoints | `T09`, `T10` | `COMPLETED` | `pytest tests/integration/test_lineage_api.py` 16 passed; full `pytest` 171 passed; `ruff` & `mypy` 0 errors; `GET /api/v1/lineage` returns 16 nodes with valid Dagre `(x, y)`; `POST /api/v1/impact/trace` matches API contract |
| `T12` | Pipeline Run History & Execution vs Quality Dual-Dimension Tracker | `T03`, `T08` | `NOT_STARTED` | — |
| `T13` | Dataset Partition Freshness & SLA Monitoring Service | `T05`, `T12` | `NOT_STARTED` | — |
| `T14` | Investigation Workspace Engine & Schema Integration | `T03`, `T08`, `T10` | `NOT_STARTED` | — |
| `T15` | Safe Report Generator Service (JSON & HTML with CSP) | `T14` | `NOT_STARTED` | — |
| `T16` | Frontend Navigation Shell, Scenario Switcher & Dataset Inspector | `T02`, `T05` | `NOT_STARTED` | — |
| `T17` | Quality Validation Findings Explorer & Evidence Drawer UI | `T08`, `T16` | `NOT_STARTED` | — |
| `T18` | Interactive Lineage DAG & Blast Radius Visualization UI | `T11`, `T16` | `NOT_STARTED` | — |
| `T19` | Pipeline Observability, Freshness & Run History UI | `T12`, `T13`, `T16` | `NOT_STARTED` | — |
| `T20` | Investigation Workspace & Report Export Modal UI | `T15`, `T17`, `T18` | `NOT_STARTED` | — |
| `T21` | Recovery Verification Backend Engine | `T08`, `T10`, `T12` | `NOT_STARTED` | — |
| `T22` | Recovery Verification Frontend View | `T20`, `T21` | `NOT_STARTED` | — |
| `T23` | Signature Scenario End-to-End Test Suite | `T01`–`T22` | `NOT_STARTED` | — |
| `T24` | Docker Compose Orchestration & Production Polish | `T23` | `NOT_STARTED` | — |

---

## 3. Current Focus & Next Steps

- **Current State:** Milestones **M0** (`T01`, `T02`), **M1** (`T03`, `T04`, `T05`), **M2** (`T06`, `T07`, `T08`), and **M3** (`T09`, `T10`, `T11`) are `COMPLETED`. Milestone **M4** is `NOT_STARTED`.
- **Next Eligible Tasks:**
  - `T12` (Pipeline Run History & Execution vs Quality Dual-Dimension Tracker) — Prerequisites satisfied (`T03`, `T08`). Initiates Milestone **M4**.
  - `T14` (Investigation Workspace Engine & Schema Integration) — Prerequisites satisfied (`T03`, `T08`, `T10`). Initiates Milestone **M5**.
  - `T16` (Frontend Navigation Shell, Scenario Switcher & Dataset Inspector) — Prerequisites satisfied (`T02`, `T05`). Initiates Milestone **M6**.

---

## 4. Completed Task Verification Log

### `T01` — Backend Scaffolding, Tooling & Base Configuration
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/pyproject.toml` with pinned dependencies (`fastapi>=0.115.0`, `uvicorn[standard]>=0.28.0`, `pydantic>=2.10.0`, `pydantic-settings>=2.2.0`, `sqlalchemy>=2.0.0`, `networkx>=3.0`, `jinja2>=3.1.0`, `python-multipart>=0.0.9`, `httpx>=0.27.0`) and dev dependencies (`ruff`, `mypy`, `pytest`, `pytest-asyncio`).
  - `backend/app/main.py` entrypoint with CORS middleware, lifespan runtime directories setup, and `/health` + `/api/v1/health` endpoints.
  - `backend/app/core/config.py` with `pydantic-settings` `Settings` class managing `LUX_` environment variables and directory resolutions.
  - `backend/app/core/errors.py` with custom exception taxonomy (`LuxException`, `NotFoundError`, `PayloadTooLargeError`) and centralized error response handlers matching the API contract standard envelope.
  - `backend/app/schemas/common.py` with `HealthResponse`, `ErrorResponse`, and `ErrorDetail` schemas.
  - Full modular monolith package layout for `api`, `core`, `db`, `models`, `schemas`, `services/{ingestion,validation,lineage,impact,pipeline,reports}`, and `storage`.
  - Base pytest suite in `backend/tests/test_health.py` and `backend/tests/conftest.py`.
  - Repository `.gitignore` preventing build artifacts and temporary files from being tracked.
- **Verification Evidence:**
  - `cd backend && pytest -v` -> 5 passed in 0.14s (`test_health_check_returns_200`, `test_api_v1_health_check_returns_200`, `test_error_envelope_on_404`, `test_cors_headers_on_preflight`, `test_async_health_check`).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 25 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 18 source files.
- **Remaining Limitations:** None. Backend scaffolding is verified and ready for database schema implementation (`T03`).

### `T02` — Frontend Scaffolding, Tooling & Lux Purple Theme Tokens
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `frontend/package.json` with React 18 (`react`, `react-dom`), Vite, Lucide React icons, Tailwind CSS v3, TypeScript, ESLint 9, and Vitest test suite.
  - `frontend/vite.config.ts` configuring `@/` path alias, `/api` proxy forwarding to backend (`http://localhost:8000`), port 3000, and Vitest jsdom test runner.
  - `frontend/tsconfig.json` with strict mode, ES2022 target, bundler module resolution, path aliases, and Vitest DOM types.
  - `frontend/tailwind.config.js` and `frontend/src/styles/tokens.css` defining the Lux Purple palette (`#6B46C1` primary, `#7C3AED` hover, `#553C9A` active, `#F3E8FF` subtle), dark slate surfaces (`#0F172A`, `#1E293B`, `#334155`), and accessible status tokens (Healthy `#10B981`, Warning `#F59E0B`, Corrupted `#F43F5E`, Neutral `#64748B`). Text on purple achieves WCAG AA & AAA contrast (6.44:1).
  - `frontend/eslint.config.js` with modern flat configuration using `typescript-eslint` and React Hooks lint rules.
  - `frontend/index.html` with dark slate base theme, SVG favicon, and meta viewport.
  - `frontend/src/App.tsx` shell featuring Lux branding, active scenario badge ("Monday Revenue Mystery"), ADR-006 dual-dimension health badges (Compute: SUCCESS vs Quality: CORRUPTED), and semantic navigation tabs (`Validations`, `Lineage`, `Impact Analysis`, `Pipelines`, `Investigation`, `Recovery`).
  - Directory structure layout matching `AGENTS.md` (`api`, `components/{common,lineage,validation,impact,reports}`, `hooks`, `types`).
  - Vitest test suite in `frontend/tests/App.test.tsx` and `frontend/tests/setup.ts`.
- **Verification Evidence:**
  - `cd frontend && npm run typecheck` -> `tsc --noEmit` exited with code 0 (0 errors).
  - `cd frontend && npm run lint` -> `eslint .` exited with code 0 (0 warnings/errors).
  - `cd frontend && npm test` -> `vitest run` 6/6 tests passed in 513ms (`tests/App.test.tsx`).
  - `cd frontend && npm test -- --run` -> `vitest run` 6/6 tests passed in 523ms (`tests/App.test.tsx`).
  - `cd frontend && npm run build` -> `tsc && vite build` completed in 4.51s, generating optimized production bundle in `frontend/dist/`.
- **Remaining Limitations:** None. Frontend foundation is operational and ready for feature view implementations.

### `T03` — Relational Database Schema & SQLite Persistence Engine
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/app/models/`: SQLAlchemy 2.0 ORM models for all 11 domain entities:
    - `Scenario` (`backend/app/models/scenario.py`): Scenario metadata, fixture version, timestamps, bidirectional relationships with cascades.
    - `Dataset` (`backend/app/models/dataset.py`): File location, format, record counts, schema definition JSON, index `idx_datasets_scenario`.
    - `ValidationRule`, `ValidationRun`, `ValidationFinding` (`backend/app/models/validation.py`): Rule configurations, runs with duration & status counts, granular findings with affected fields, evidence JSON, and declared indices.
    - `LineageNode`, `LineageEdge` (`backend/app/models/lineage.py`): Directed DAG nodes with metadata mapped to DB column `metadata` (aliased as `node_metadata` to avoid `DeclarativeBase.metadata` conflict), directional edges, indices `idx_nodes_scenario`, `idx_edges_scenario`, `idx_edges_source`, `idx_edges_target`.
    - `PipelineRun`, `FreshnessCheck` (`backend/app/models/pipeline.py`): Pipeline compute execution status vs data quality dimension tracking, duration, step logs, partition freshness SLA checkpoints.
    - `Investigation`, `ReportArtifact` (`backend/app/models/investigation.py`): Incident workspace facts/hypotheses/remediation, initial finding linkage, and generated JSON/HTML reports with sha256 checksums.
  - `backend/app/db/session.py`: Database engine with SQLite connection event listener enforcing `PRAGMA journal_mode=WAL;`, `PRAGMA foreign_keys=ON;`, and `PRAGMA busy_timeout=5000;`. Provided `SessionLocal` factory and `get_db` FastAPI dependency.
  - `backend/app/db/init_db.py`: Database initialization utility creating all 11 tables and indices, ensuring data directories exist, and wired into FastAPI lifespan startup hook.
  - `backend/tests/integration/test_db.py`: Comprehensive 9-test integration suite verifying SQLite pragmas (WAL mode, FKs, busy timeout), all 11 tables and indices, CRUD across all entities, foreign key constraint enforcement, scenario cascade deletes, dataset cascade deletes and `SET NULL` on lineage nodes, finding deletion `SET NULL` on investigations, and report artifact cascade deletes.
- **Verification Evidence:**
  - `cd backend && pytest tests/integration/test_db.py -v` -> 9 passed in 1.19s.
  - `cd backend && pytest -v` -> 14 passed in 1.10s (5 health tests + 9 database integration tests).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 35 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 27 source files.
  - `cd frontend && npm test -- --run` -> Vitest 6/6 passed in 947ms (no regressions).
- **Remaining Limitations:** None. SQLite persistence engine and ORM models are operational and ready for scenario fixtures and data ingestion (`T04` & `T05`).

### `T04` — Bundled Signature Fixtures & Scenario Metadata Definition
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `data/scenarios/monday_revenue_mystery/`:
    - `scenario.json`: Complete scenario metadata, 4 dataset schemas (`orders`, `order_items`, `products`, `inventory`), and 16-node lineage DAG with 14 edges matching `docs/data-model.md`. Verified strictly acyclic via NetworkX.
    - `rules.json`: Declarative quality rules catalog including the 4 target defect rules (`VAL-ORD-001`, `VAL-ORD-002`, `VAL-INV-001`, `VAL-FRESH-001`) and 4 baseline passing rules (`VAL-ORD-003`, `VAL-PRD-001`, `VAL-PRD-002`, `VAL-INV-002`).
    - `pipeline_history.json`: Historical pipeline runs tracking compute `COMPLETED_SUCCESS` alongside quality `CORRUPTED`, run logs, and partition freshness SLA checkpoints (`STALE` on defective orders).
    - `defective/`:
      - `orders.csv`: Exactly 1,250 rows; 15 duplicate order IDs; $142,000 revenue spike calibration; 4-hour temporal gap (0 orders between Sunday 18:00 and 22:00 UTC).
      - `order_items.csv`: Exactly 3,420 rows; exactly 24 orphaned items referencing non-existent product IDs (`PRD-9001` through `PRD-9024`).
      - `products.csv`: Exactly 250 rows with unique `product_id` and positive prices.
      - `inventory.csv`: Exactly 250 rows; exactly 8 SKUs with negative `quantity_on_hand`.
    - `corrected/`:
      - `orders.csv`: Exactly 1,250 rows; 0 duplicate order IDs (1,250 unique IDs); Sunday 18:00–22:00 UTC temporal gap resolved with 15 regular orders.
      - `order_items.csv`: Exactly 3,420 rows; 0 orphaned items (all referencing valid `product_id`).
      - `products.csv`: Exactly 250 rows with unique `product_id`.
      - `inventory.csv`: Exactly 250 rows; 0 negative inventory rows (`quantity_on_hand >= 0`).
      - `pipeline_history.json`: Successful run reflecting `HEALTHY` quality dimension and `FRESH` partition SLA.
  - `backend/app/services/ingestion/scenario_fixtures.py`: Deterministic generator script using seed 42 to synthesize and output all CSV and JSON fixtures with UTF-8 encoding, LF line endings, and no BOM.
  - `backend/tests/unit/test_fixtures.py`: Comprehensive 8-test unit suite verifying file encoding, LF line endings, metadata schemas, lineage DAG acyclicity, pipeline history, exact row counts, defective fixture anomalies, corrected fixture recovery, and generator determinism.
- **Verification Evidence:**
  - `cd backend && pytest tests/unit/test_fixtures.py -v` -> 8 passed in 1.18s.
  - `cd backend && pytest -v` -> 22 passed in 2.17s (5 health + 9 db integration + 8 fixtures unit).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 37 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 28 source files.
  - `cd frontend && npm test -- --run` -> Vitest 6/6 passed in 881ms (no regressions).
- **Remaining Limitations:** None. Fixtures and metadata are generated, verified, and ready for ingestion service loading (`T05`).

### `T05` — Dataset Ingestion, Scenario Loader & Upload Security Service
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/app/schemas/dataset.py`: Pydantic domain models for datasets (`DatasetResponse`, `DatasetPreviewResponse`, `DatasetUploadResponse`, `ColumnSchema`).
  - `backend/app/schemas/scenario.py`: Pydantic models for scenario catalog and lifecycle (`ScenarioSummary`, `ScenarioDetail`, `LoadScenarioRequest`, `LoadScenarioResponse`).
  - `backend/app/services/ingestion/reader.py`: `DatasetReader` streaming engine supporting chunked CSV and JSON inspection, column type inference, record counts, and strictly paginated preview rows (capped at 100 rows per request per `docs/security.md`).
  - `backend/app/services/ingestion/security.py`: File upload security handler enforcing 20MB file size limit (`PayloadTooLargeError` HTTP 413), strict extension whitelist (`.csv`, `.json`), path traversal prevention (rejecting `..`, `/`, `\\`, and raw/URL-encoded null bytes with HTTP 400), content sniffing (rejecting binary streams, null bytes, zip archives), and isolated UUID directory isolation in `data/uploads/{uuid4()}/`.
  - `backend/app/services/ingestion/loader.py`: `ScenarioLoaderService` parsing bundled scenario metadata (`scenario.json`), quality rules catalog (`rules.json`), and pipeline history (`pipeline_history.json`), and idempotently loading into SQLite entities (`Scenario`, `Dataset`, `ValidationRule`, `LineageNode`, `LineageEdge`, `PipelineRun`, `FreshnessCheck`). Supports both `"defective"` and `"corrected"` recovery fixtures.
  - `backend/app/api/v1/`: Modular FastAPI endpoints:
    - `GET /api/v1/scenarios`: Enumerate bundled scenarios with dataset and rule counts.
    - `GET /api/v1/scenarios/{id}`: Detailed scenario configuration and dataset descriptors.
    - `POST /api/v1/scenarios/{id}/load`: Idempotent scenario fixture loader with versioning.
    - `GET /api/v1/datasets`: List all datasets, filterable by `scenario_id`.
    - `GET /api/v1/datasets/{id}`: Retrieve dataset metadata.
    - `GET /api/v1/datasets/{id}/preview`: Paginated row viewer with limit and offset.
    - `POST /api/v1/datasets/upload`: Multipart dataset upload with complete security guardrails.
  - `backend/tests/integration/test_ingestion_api.py`: 14-test integration test suite covering scenario loading, preview row pagination, upper bound limits, 404 error envelopes, oversized file rejection (HTTP 413), path traversal attack rejection (HTTP 400), extension whitelist enforcement, custom dataset upload and preview, and recovery reloading.
  - `backend/tests/unit/test_ingestion_service.py`: 7-test unit suite validating type inference, value casting, filename validation, and content sniffing.
- **Verification Evidence:**
  - `cd backend && pytest tests/integration/test_ingestion_api.py -v` -> 14 passed in 1.98s.
  - `cd backend && pytest tests/unit/test_ingestion_service.py -v` -> 7 passed in 0.03s.
  - `cd backend && pytest -v` -> 43 passed in 4.08s (all test suites passing).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 48 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 37 source files.
  - `cd frontend && npm test -- --run` -> Vitest 6/6 passed in 899ms (zero frontend regressions).
- **Remaining Limitations:** None. Ingestion service, scenario loader, upload security, and dataset preview APIs are fully operational and verified. Milestone M1 is complete. Ready for Milestone M2 (`T06` - Validation Rule Framework).

### `T06` — Validation Rule Framework & Core Rule Evaluators
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/app/schemas/validation.py`: Pydantic domain models and enums (`RuleCategory`, `RuleSeverity`, `RuleStatus`, `ValidationRuleConfig`, `RuleEvaluationResult`).
  - `backend/app/services/validation/base.py`:
    - `ValidationContext`: Dataset execution context supporting in-memory records as well as streaming from CSV and JSON files, record count caching, and cross-dataset context.
    - `BaseValidationRule`: Abstract base class implementing the template method pattern: automatic duration measurement in milliseconds, structured finding formatting (`_build_result`), active status checks, and resilient exception handling (recording `ERROR` status without engine crashes).
  - `backend/app/services/validation/core.py`: Core rule evaluators:
    - `NullCheckRule`: Detects nulls, empty strings, and whitespace-only cells (strictly stripped) across single or multiple required columns.
    - `UniquenessRule`: Validates single primary keys and multi-column composite keys; aggregates duplicate occurrences and collects sample duplicates with line indices and keys.
    - `TypeValidityRule`: Verifies parseability for integers, floats, booleans, ISO-8601 timestamps, and JSON, as well as full-match regex patterns, with configurable `allow_null` behavior.
    - `RecordCountRule`: Verifies dataset row count bounds against `min_count`, `max_count`, and `exact_count` expectations.
    - `ValueRangeRule`: Asserts numeric lower and upper bounds with configurable inclusive/exclusive boundary checks (`inclusive_min`, `inclusive_max`) and `allow_null` handling.
  - `backend/app/services/validation/registry.py`: `RuleRegistry` providing dynamic rule lookup, registration decorator (`@register_rule`), and factory instantiation (`create_rule`) supporting dictionaries, Pydantic schemas, and SQLAlchemy ORM models, with graceful handling of SQLite JSON-serialized parameters.
  - `backend/tests/unit/test_rules_core.py`: 38-test unit suite validating all core evaluators, context streaming, registry factory mechanics, composite keys, whitespace edge cases, and signature acceptance criteria.
- **Verification Evidence:**
  - `UniquenessRule` on defective `orders.csv`: Accurately detected 15 duplicate records across 15 distinct keys, with exact row indices (e.g. `ORD-0015` at indices 14 and 1235). Passed with 0 duplicates on corrected `orders.csv`.
  - `ValueRangeRule` on defective `inventory.csv`: Accurately detected 8 negative inventory SKUs with exact negative values and reasons (e.g. `SKU-0012` at index 11 with quantity -12). Passed with 0 violations on corrected `inventory.csv`.
  - `cd backend && pytest tests/unit/test_rules_core.py -v` -> 38 passed in 0.18s.
  - `cd backend && pytest` -> 81 passed in 3.04s (all test suites passing).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 53 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 41 source files.
  - `cd frontend && npx vitest run` -> 6/6 passed in 612ms (zero frontend regressions).
- **Remaining Limitations:** None. Core validation framework and evaluators are operational and tested. Ready for advanced relational, temporal, and schema evaluators (`T07`).

### `T07` — Relational, Temporal & Schema Rule Evaluators
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/app/services/validation/base.py`:
    - Enhanced `ValidationContext` with `get_dataset_records(target_dataset_id)` and `get_dataset_records_as_list(target_dataset_id)` supporting cross-dataset resolution across in-memory datasets, `ValidationContext` instances, explicit file paths, and sibling directory resolutions.
  - `backend/app/services/validation/relational.py`: Advanced rule evaluators:
    - `ReferentialIntegrityRule`: Validates foreign key relationships across datasets using in-memory set lookups ($O(1)$ complexity) for single and composite foreign keys, configurable `allow_null` behavior, sample orphaned keys collection, and detailed violation payloads.
    - `TemporalAnomalyRule`: Parses ISO-8601 timestamps, detects future timestamps against reference time, enforces `min_date` and `max_date` bounds, and scans for chronological temporal gaps exceeding configurable `max_gap_hours`.
    - `SchemaIntegrityRule`: Asserts column existence, detects missing expected columns, rejects unexpected columns when `allow_extra_columns=False`, enforces column ordering when `strict_order=True`, and samples rows to identify data type drift across integer, float, boolean, and timestamp columns.
    - `FreshnessRule`: Evaluates partition recency against SLA thresholds (`sla_hours`), detects missing transaction windows via `max_gap_hours`, and computes status (`FRESH` vs `STALE`).
  - `backend/app/services/validation/registry.py`:
    - Registered all four advanced evaluators into `RuleRegistry` for categories `REFERENTIAL_INTEGRITY`, `TEMPORAL_ANOMALY`, `SCHEMA_INTEGRITY`, and `FRESHNESS`.
  - `backend/app/services/validation/__init__.py`:
    - Exported all new rule evaluators in public package interface.
  - `backend/tests/unit/test_rules_relational.py`:
    - 25-test comprehensive unit suite validating all 4 evaluators, composite keys, null handling, type drift, and signature scenario acceptance criteria.
- **Verification Evidence:**
  - `ReferentialIntegrityRule` on defective `order_items.csv` vs `products.csv`: Accurately detected all 24 orphaned records (`PRD-9001` through `PRD-9024`), with parent key count 250 and total 3,420 records evaluated. Passed with 0 orphaned items on corrected fixtures.
  - `TemporalAnomalyRule` on defective `orders.csv`: Accurately detected Sunday evening temporal gap (from 2026-10-18T17:58:01 to 2026-10-18T22:26:00, 4.47 hours > 4.0h threshold). Passed on corrected `orders.csv` (max observed gap 0.68 hours).
  - `FreshnessRule` on `VAL-FRESH-001`: Accurately flagged defective `orders.csv` as `STALE` due to 4.47h gap > 4h threshold. Passed with `FRESH` status on corrected `orders.csv`.
  - `cd backend && pytest tests/unit/test_rules_relational.py -v` -> 25 passed in 0.33s.
  - `cd backend && pytest` -> 106 passed in 4.28s (all test suites passing).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 55 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 42 source files.
  - `cd frontend && npm test -- --run` -> Vitest 6/6 passed in 975ms (zero frontend regressions).
- **Remaining Limitations:** None. Relational, temporal, schema, and freshness evaluators are fully operational and verified. Ready for the validation runner service and structured findings API (`T08`).

### `T08` — Validation Runner Service, Persistence & Structured Findings API
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/app/services/validation/runner.py`:
    - `ValidationRunnerService`: Orchestrates quality validation runs against scenario datasets.
    - Dataset context caching with cross-dataset accessibility for relational integrity evaluation.
    - Rule discovery and execution through dynamic `RuleRegistry` evaluators.
    - Bounded diagnostic evidence capping (`_cap_evidence_samples`) ensuring sample arrays (e.g. duplicate keys, orphaned records) do not exceed 50 items.
    - Dual-dimension status derivation: maps failed or runtime error checks to run status `FAILED`, non-fatal checks to `WARNING`, and clean evaluations to `PASSED`.
    - SQLite persistence for `ValidationRun` and granular `ValidationFinding` records with transactional rollback on failure.
    - Filterable and paginated findings retrieval (`severity`, `status`, `dataset_id`, `limit`, `offset`).
  - `backend/app/schemas/validation.py` & `backend/app/schemas/__init__.py`:
    - `ValidationRunRequest`: Payload schema supporting scenario specification and optional target dataset filters.
    - `ValidationRunResponse`: Full run execution summary conforming to API contracts.
    - `ValidationFindingItem`: Structured finding schema with parsed diagnostic evidence and rule metadata.
    - `ValidationFindingsListResponse`: Paginated findings envelope with total count and finding items.
    - `ValidationRunListResponse`: Historical run list response schema.
  - `backend/app/api/v1/validations.py` & `backend/app/api/v1/router.py`:
    - `POST /api/v1/validations/run`: Triggers validation run for all or selected datasets.
    - `GET /api/v1/validations/runs/{id}`: Retrieves validation run execution summary.
    - `GET /api/v1/validations/runs`: Lists historical runs with optional scenario filter.
    - `GET /api/v1/validations/runs/{id}/findings`: Returns granular findings filterable by severity, status, and dataset.
  - `backend/tests/integration/test_validations_api.py`:
    - 14-test integration suite asserting full API contracts, acceptance criteria, defective fixture defect counts, clean recovery validation, filtering, pagination, and error envelopes.
- **Verification Evidence:**
  - Defective *Monday Revenue Mystery* execution: Executed all 8 checks, yielding exactly 4 failed checks and 4 passed checks with overall status `FAILED`:
    - `VAL-ORD-001`: 15 duplicate order IDs detected with line indices.
    - `VAL-ORD-002`: 24 broken foreign keys detected with sample orphaned keys (`PRD-9001` to `PRD-9024`).
    - `VAL-INV-001`: 8 negative inventory quantities detected.
    - `VAL-FRESH-001`: Sunday 4.47h transaction gap flagged.
  - Corrected fixture execution: Executed all 8 checks, yielding 8 passed checks, 0 failures, and overall status `PASSED`.
  - Evidence capping: Bounded large error sets (>100 items) to 50 sample items with truncation flags.
  - `cd backend && pytest tests/integration/test_validations_api.py -v` -> 14 passed in 2.62s.
  - `cd backend && pytest` -> 120 passed in 6.34s (all unit & integration tests passing).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 58 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 44 source files.
  - `cd frontend && npm test -- --run` -> Vitest 6/6 passed in 866ms (zero frontend regressions).
- **Remaining Limitations:** None. Validation engine and REST endpoints are verified and ready for downstream impact tracing (`T10`), lineage DAG integration (`T09`), pipeline history tracking (`T12`), and UI findings explorer (`T17`).

### `T09` — Lineage DAG Domain Engine & Graph Integrity Validator
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/app/core/errors.py`:
    - Added `CyclicDependencyError` (subclassing `LuxException` with HTTP 400, structured `code="CYCLIC_DEPENDENCY"`, and `cycle_path` attribute/detail list).
    - Added `LineageIntegrityError` (subclassing `LuxException` with HTTP 400, structured `code="LINEAGE_INTEGRITY_ERROR"`, capturing dangling references and graph integrity violations).
  - `backend/app/schemas/lineage.py` & `backend/app/schemas/__init__.py`:
    - `LineageNodeType` (`StrEnum`): `SOURCE_DATASET`, `TRANSFORMATION`, `DERIVED_DATASET`, `METRIC`, `REPORT`.
    - `LineageNode`: Pydantic model capturing unique ID, name, classification type, optional dataset foreign key, owner, description, execution status, quality health, and JSON-parsed metadata.
    - `LineageEdge`: Pydantic model capturing edge ID, source ID, target ID, and dependency type.
    - `LineageGraphSchema`: Composite schema for graph payload serialization.
    - `GraphValidationSummary`: Diagnostic validation summary returning `is_valid`, `is_dag`, `cycles`, `dangling_edges`, `isolated_nodes`, `errors`, and `warnings`.
  - `backend/app/services/lineage/graph.py` & `backend/app/services/lineage/__init__.py`:
    - `LineageGraph`: NetworkX `DiGraph` encapsulation providing strict DAG domain operations.
    - Graph integrity validation:
      - `validate_integrity()`: Non-throwing comprehensive structural validator evaluating acyclicity (`nx.is_directed_acyclic_graph`), extracting simple cycles (`nx.simple_cycles`), flagging dangling edges (referencing unregistered nodes), and categorizing isolated nodes (`nx.isolates`).
      - `validate()`: Raising `CyclicDependencyError` with the cycle path loop or `LineageIntegrityError` on invalid graph topologies.
    - Traversal & dependency queries:
      - `get_upstream_nodes()`: Transitive upstream ancestor discovery (`nx.ancestors`).
      - `get_downstream_nodes()`: Transitive downstream descendant discovery (`nx.descendants`).
      - `get_upstream_dataset_ids()`: Resolution of ancestor nodes to underlying storage dataset IDs (`orders`, `order_items`, `products`).
      - `get_direct_upstream()` / `get_direct_downstream()`: Immediate predecessor and successor inspection.
      - `topological_sort()`: Topological ordering of nodes (`nx.topological_sort`).
      - `has_path()` / `get_shortest_path()` / `get_all_paths()`: Path connectivity and routing.
      - `get_root_nodes()` / `get_terminal_nodes()` / `get_isolated_nodes()`: Boundary node analysis.
      - `get_subgraph()`: Induced subgraph extraction.
    - Seed loaders & factory methods:
      - `from_scenario_dict()`: Ingests `scenario.json` metadata dict with optional validation.
      - `from_scenario_file()`: Loads scenario graph directly from filesystem JSON.
      - `from_db()`: Seeds `LineageGraph` from SQLite database entities (`LineageNode`, `LineageEdge`).
      - `to_dict()` & `to_schema()`: Clean serialization.
  - `backend/tests/unit/test_lineage_graph.py`:
    - 22-test unit test suite asserting 16-node / 14-edge scenario graph loading from file and DB, upstream ancestor resolution to `orders` and `order_items`, downstream descendant path traversal to `report_exec_dash`, cycle rejection (self-loops, 2-node loops, multi-hop loops), dangling edge detection, isolated node handling, topological sort verification, path queries, and error boundaries.
- **Verification Evidence:**
  - `cd backend && pytest tests/unit/test_lineage_graph.py -v` -> 22 passed in 0.80s.
  - `cd backend && pytest` -> 142 passed in 4.98s (100% of unit and integration test suite passing).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 61 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 46 source files.
  - `cd frontend && npm test -- --run` -> Vitest 6/6 passed in 473ms (zero frontend regressions).
- **Remaining Limitations:** None. Lineage graph engine is verified and ready for downstream impact analysis engine (`T10`), REST endpoints (`T11`), and frontend interactive DAG visualizer (`T18`).

### `T10` — Downstream Impact Analysis Engine & Blast Radius Classifier
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/app/schemas/impact.py` & `backend/app/schemas/__init__.py`:
    - `AssetImpactStatus` (`StrEnum`): `CONFIRMED_FAILED`, `DIRECTLY_AFFECTED`, `POTENTIALLY_AFFECTED`, `HEALTHY` (ADR-006).
    - `ImpactTargetType` (`StrEnum`): `FINDING`, `DATASET`, `NODE`, `RULE`, `AUTO`.
    - `AffectedAsset`: Pydantic model capturing unique `node_id`, human-readable `name`, `type`, `impact_status`, graph `distance` (hops), complete `dependency_path` (node IDs), `dependency_path_names` (labels), and breadcrumb `explanation`.
    - `ImpactSummary`: Breakdown of affected asset counts by tier (`confirmed_failed`, `directly_affected`, `potentially_affected`, `healthy`).
    - `ImpactTraceRequest` & `BlastRadiusReport`: Comprehensive request/response models conforming to REST API specifications and API contracts.
  - `backend/app/services/impact/analyzer.py` & `backend/app/services/impact/__init__.py`:
    - `ImpactAnalysisService`: Pure domain service encapsulating downstream blast radius traversal, multi-target resolution, classification logic, and breadcrumb path building:
      - `resolve_target_node()`: Multi-strategy target resolver resolving node IDs (`src_orders`), file names (`orders.csv`), dataset IDs (`orders`), validation rule IDs (`VAL-ORD-001`), database `ValidationFinding` records, or scenario definitions.
      - `trace_impact()`: Traces directed paths through `LineageGraph`, categorizes direct vs transitive downstream consumers, determines graph distance, builds dependency breadcrumb explanations, handles inclusion/exclusion of transformation steps and root entities, and sorts outputs deterministically by distance and node ID.
      - `classify_graph_nodes()`: Evaluates and annotates the entire lineage graph with dual-dimension quality statuses, marking confirmed failures, direct/transitive impacts, and unaffected nodes as `HEALTHY`.
      - `build_path_explanation()`: Formats human-readable dependency breadcrumb strings.
      - `get_root_cause_candidates()`: Discovers candidate upstream origin sources feeding into any given node.
  - `backend/tests/unit/test_impact_analysis.py`:
    - 13-test unit test suite verifying:
      - `orders.csv` blast radius identifies `dim_orders` as `DIRECTLY_AFFECTED` (distance 2), and `agg_daily_revenue`, `metric_revenue`, `report_exec_dash` as `POTENTIALLY_AFFECTED` (distance 4, 5, 6).
      - Step-by-step breadcrumb explanations matching `orders.csv -> transform_clean_orders -> dim_orders -> ... -> Report: Executive Monday Dashboard`.
      - Target format equivalence (`orders.csv` == `orders` == `src_orders`).
      - Rule ID resolution (`VAL-ORD-001`).
      - Database `ValidationFinding` lookup and resolution.
      - Alternative pipeline branch isolation (`order_items.csv` and `inventory.csv`).
      - `include_transformations` flag including intermediate compute steps (`tf_orders`, `tf_revenue`).
      - `include_root` flag omitting root entity when requested.
      - Terminal/leaf node tracing (`report_exec_dash` having 0 downstream assets).
      - Full-graph node classification (`classify_graph_nodes`) marking unaffected nodes as `HEALTHY`.
      - Candidate root cause discovery (`get_root_cause_candidates`).
      - `NotFoundError` boundary handling for unresolvable targets.
      - Multi-path graph topologies (shortest path selection and item deduplication).
- **Verification Evidence:**
  - `cd backend && pytest tests/unit/test_impact_analysis.py -v` -> 13 passed in 1.17s.
  - `cd backend && pytest` -> 155 passed in 7.37s (100% test suite passing, zero regressions).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 64 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 48 source files.
- **Remaining Limitations:** None. Downstream impact analysis engine is verified and ready for REST API exposure in `T11` and downstream integration in `T14` (Investigation Workspace) and `T21` (Recovery Verification).

### `T11` — Lineage & Impact REST API Endpoints
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/app/schemas/lineage.py` & `backend/app/schemas/__init__.py`:
    - `NodePosition`: Layout position model (`x: float`, `y: float`) formatted for React Flow visualizer.
    - `ReactFlowNode`: Flow node model with unique `id`, `name`, `type`, `dataset_id`, dual-dimension statuses (`execution_status`, `quality_health`), `position`, metadata, and `data` dictionary.
    - `ReactFlowEdge`: Flow edge model with `id`, `source`, `target`, `dependency_type`, and dynamic `animated` flag for corrupted dependency paths.
    - `LineageGraphResponse`: Complete graph payload containing scenario ID, nodes, and edges.
    - `LineageNodeSummary`: Compact node summary for predecessor and successor connections.
    - `LineageNodeDetailResponse`: Detailed node metadata model with direct upstream/downstream connections, ancestor/descendant counts, and upstream root storage dataset IDs.
    - `LineageValidateRequest`: Request schema supporting scenario-based or custom ad-hoc node/edge validation.
  - `backend/app/services/lineage/layout.py` & `backend/app/services/lineage/__init__.py`:
    - `compute_dagre_layout()`: Hierarchical Sugiyama/Dagre layout algorithm computing non-colliding (x, y) coordinates:
      - Assigns integer ranks via longest-path layering in topological order.
      - Orders nodes within each rank using the predecessor barycenter heuristic to untangle edge crossings.
      - Places nodes along the horizontal axis by rank (`x = margin_x + rank * rank_sep`) and vertical axis centered on predecessor barycenters with minimum `node_sep` collision enforcement.
      - Graceful fallback for non-DAG topologies.
    - `build_flow_graph()`: Assembles `LineageGraphResponse` from a domain `LineageGraph` with Dagre layout coordinates and dynamic status annotations.
  - `backend/app/api/v1/lineage.py`:
    - `GET /api/v1/lineage`: Returns 16 nodes and 14 edges formatted for React Flow with valid numeric `position.x` and `position.y`, dynamically annotating `quality_health` based on executed validation runs.
    - `GET /api/v1/lineage/nodes/{id}`: Returns comprehensive node metadata, direct predecessors and successors, upstream dataset IDs, and connection counts. Returns 404 with standard error envelope if node is not found.
    - `POST /api/v1/lineage/validate`: Evaluates graph integrity (cycles, dangling edges, isolated nodes), returning `GraphValidationSummary`.
  - `backend/app/api/v1/impact.py`:
    - `POST /api/v1/impact/trace`: Calculates downstream blast radius from target ID (dataset, finding, rule, or node), returning `BlastRadiusReport` with affected asset paths, distance, and tier breakdowns.
  - `backend/app/api/v1/router.py`:
    - Included `lineage_router` and `impact_router` into master v1 API router.
  - `backend/tests/integration/test_lineage_api.py`:
    - 16-test comprehensive integration suite verifying:
      - `GET /api/v1/lineage` returns exactly 16 nodes and 14 edges with valid numeric `position.x` and `position.y`.
      - Topological Left-to-Right layout property: `x(upstream) < x(downstream)`.
      - Non-colliding node coordinates across parallel pipeline branches.
      - Dynamic `quality_health` annotation (`CORRUPTED` vs `HEALTHY`) after validation execution, including edge animation.
      - Default scenario resolution to `monday_revenue_mystery`.
      - 404 error envelope when scenario does not exist.
      - `GET /api/v1/lineage/nodes/{id}` for root source node (`src_orders`) and leaf report node (`report_exec_dash`).
      - 404 error envelope when node ID does not exist.
      - `POST /api/v1/lineage/validate` for valid scenario graph.
      - Detection of cyclic ad-hoc dependencies with structured cycle paths.
      - Detection of dangling edges referencing unregistered nodes.
      - `POST /api/v1/impact/trace` from dataset `orders.csv` returning expected affected assets (`CONFIRMED_FAILED`, `DIRECTLY_AFFECTED`, `POTENTIALLY_AFFECTED`).
      - Impact tracing from validation rule ID (`VAL-ORD-001`).
      - Impact tracing branch isolation from inventory node (`src_inventory`).
      - Leaf node tracing with zero downstream descendants.
      - `include_transformations` parameter inclusion.
      - 404 error envelope when target entity cannot be resolved.
- **Verification Evidence:**
  - `cd backend && pytest tests/integration/test_lineage_api.py -v` -> 16 passed in 1.94s.
  - `cd backend && pytest` -> 171 passed in 6.47s (100% unit and integration test suite passing).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 68 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 51 source files.
  - `cd frontend && npm run typecheck` -> `tsc --noEmit` exited with code 0 (0 errors).
  - `cd frontend && npm run lint` -> `eslint .` exited with code 0 (0 warnings/errors).
  - `cd frontend && npm test -- --run` -> Vitest 6/6 passed in 529ms (zero frontend regressions).
  - `cd frontend && npm run build` -> `tsc && vite build` built in 3.93s, generating production bundle.
- **Remaining Limitations:** None. Lineage and Impact REST API endpoints are fully operational, concluding Milestone **M3**. The system is ready for Milestone **M4** (`T12`: Pipeline Run History & Execution vs Quality Dual-Dimension Tracker), Milestone **M5** (`T14`: Investigation Workspace Engine), and Milestone **M6** (`T16` & `T18`: Interactive Lineage DAG UI).





