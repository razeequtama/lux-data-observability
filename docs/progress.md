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
| **M4** | Pipeline Observability & Run History | `T12`, `T13` | `COMPLETED` |
| **M5** | Incident Investigation & Safe Report Generation | `T14`, `T15` | `COMPLETED` |
| **M6** | Frontend "Trace the Failure" Interactive UI | `T16`, `T17`, `T18`, `T19`, `T20` | `COMPLETED` |
| **M7** | Recovery Verification & End-to-End Acceptance | `T21`, `T22`, `T23` | `COMPLETED` |
| **M8** | Containerization & Operational Polish | `T24` | `COMPLETED` |

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
| `T12` | Pipeline Run History & Execution vs Quality Dual-Dimension Tracker | `T03`, `T08` | `COMPLETED` | `pytest tests/integration/test_pipeline_api.py` 8 passed; full `pytest` 187 passed; `ruff` & `mypy` 0 errors; overnight run verified with `COMPLETED_SUCCESS` compute vs `CORRUPTED` quality health; step logs & pagination verified |
| `T13` | Dataset Partition Freshness & SLA Monitoring Service | `T05`, `T12` | `COMPLETED` | `pytest tests/integration/test_freshness_api.py` 5 passed; full `pytest` 199 passed; `ruff` & `mypy` 0 errors; `GET /api/v1/pipelines/freshness` identifies `orders.csv` as `STALE` (5.99h behind SLA); clean recovery and missing timestamp edge cases verified |
| `T14` | Investigation Workspace Engine & Schema Integration | `T03`, `T08`, `T10` | `COMPLETED` | `pytest tests/integration/test_investigations_api.py` 9 passed; full `pytest` 218 passed; `ruff` & `mypy` 0 errors; verified facts, hypotheses, and action items persisted; fact-hypothesis boundary enforced; empty action items handled cleanly |
| `T15` | Safe Report Generator Service (JSON & HTML with CSP) | `T14` | `COMPLETED` | `pytest tests/unit/test_report_sanitization.py tests/integration/test_reports_api.py` 17 passed; full `pytest` 235 passed; `ruff` & `mypy` 0 errors; XSS autoescape, CSP header, SHA-256 integrity, inlined Lux Purple CSS, native `<details>` evidence panels, and JSON/HTML export verified |
| `T16` | Frontend Navigation Shell, Scenario Switcher & Dataset Inspector | `T02`, `T05` | `COMPLETED` | `vitest` 34 passed (6 test files); `tsc` & `eslint` 0 errors; production build verified (186.84 kB); scenario switcher, dataset inspector, paginated preview modal, and drag-and-drop upload with 20MB limit verified |
| `T17` | Quality Validation Findings Explorer & Evidence Drawer UI | `T08`, `T16` | `COMPLETED` | `vitest` 62 passed (11 test files); `tsc` & `eslint` 0 errors; production build verified (229.35 kB); summary cards, severity/status filters, CRITICAL isolation of duplicate orders, slide-over evidence drawer with focus trap & sample row line numbers, and Trace Impact action verified |
| `T18` | Interactive Lineage DAG & Blast Radius Visualization UI | `T11`, `T16` | `COMPLETED` | `vitest` 83 passed (15 test files); `tsc` & `eslint` 0 errors; production build verified (451.95 kB); all 16 nodes rendered with Dagre coordinates, custom dual-status chips (Compute Exit 0 vs Quality Corrupted), selecting src_orders highlights downstream blast radius through to report_exec_dash, and NodeDetailsPanel verified |
| `T19` | Pipeline Observability, Freshness & Run History UI | `T12`, `T13`, `T16` | `COMPLETED` | `vitest` 108 passed (20 test files); `tsc` & `eslint` 0 errors; production build verified (480.13 kB); overnight run verified with `COMPLETED_SUCCESS` compute badge alongside `CORRUPTED` data health badge; `orders.csv` partition staleness (5.99h behind SLA) and dual-dimension callout verified |
| `T20` | Investigation Workspace & Report Export Modal UI | `T15`, `T17`, `T18` | `COMPLETED` | `vitest` 128 passed (24 test files); `tsc` & `eslint` 0 errors; production build verified (514.83 kB); 3 boundary zones (facts, hypotheses, actions), automatic synthesis from findings & pipeline, report generation with sandboxed HTML iframe & formatted JSON preview, direct file downloads with blob URL memory cleanup verified |
| `T21` | Recovery Verification Backend Engine | `T08`, `T10`, `T12` | `COMPLETED` | `pytest tests/integration/test_recovery_api.py tests/unit/test_recovery_service.py` 9 passed; full `pytest` 245 passed; `ruff` and `mypy` 0 errors; 4 defects resolved, quality health transitions to HEALTHY, downstream ALL_ASSETS_HEALTHY |
| `T22` | Recovery Verification Frontend View | `T20`, `T21` | `COMPLETED` | `vitest` 145 passed (29 test files); `tsc` & `eslint` 0 errors; production build verified (545.45 kB); side-by-side run comparison, resolution checklist with green checkmarks, downstream recovery banner confirming trust restored in reports verified |
| `T23` | Signature Scenario End-to-End Test Suite | `T01`–`T22` | `COMPLETED` | `pytest tests/scenarios/test_monday_revenue_mystery.py` 9 passed; master E2E runs in 1.13s (< 2s acceptance threshold); full `pytest` 254 passed; `ruff` & `mypy` 0 errors; 100% assertions pass across all 8 stages |
| `T24` | Docker Compose Orchestration & Production Polish | `T23` | `COMPLETED` | `docker compose build` 0 errors; full stack (`backend:8000`, `frontend:3000`) healthy; Nginx reverse proxy, SQLite WAL volume mount, 8-stage scenario workflow verified; `README.md` updated |

---

## 3. Current Focus & Next Steps

- **Current State:** All Milestones from **M0** through **M8** (`T01`–`T24`) are `COMPLETED`. The entire Lux Data Observability Platform is fully implemented, containerized, verified, and operational.
- **Next Eligible Tasks:**
  - None. All 24 implementation backlog tasks are 100% complete. Platform is ready for operational evaluation and production container deployment.

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

### `T12` — Pipeline Run History & Execution vs Quality Dual-Dimension Tracker
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/app/schemas/pipeline.py`:
    - Enums: `PipelineExecutionStatus` (`COMPLETED_SUCCESS`, `COMPLETED_WITH_WARNINGS`, `FAILED`, `RUNNING`, `CANCELLED`) and `QualityHealthStatus` (`HEALTHY`, `WARNING`, `DEGRADED`, `CORRUPTED`, `UNVALIDATED`) per ADR-006.
    - Pydantic models: `PipelineStepLog` (step name, status, record count, execution duration) and `PipelineRunResponse` with `from_model` classmethod handling JSON step log deserialization with fallback.
  - `backend/app/schemas/__init__.py`:
    - Exported `PipelineExecutionStatus`, `QualityHealthStatus`, `PipelineStepLog`, and `PipelineRunResponse`.
  - `backend/app/services/pipeline/service.py`:
    - `PipelineHistoryService`:
      - `get_runs`: Historical pipeline execution retrieval, descending chronological ordering, pagination (`limit`, `offset`), and scenario filtering.
      - `get_run_by_id`: Single pipeline run lookup with structured 404 `PIPELINE_RUN_NOT_FOUND` error handling.
      - `evaluate_quality_health`: Deterministic ADR-006 rule evaluator determining quality status (`UNVALIDATED` -> `CORRUPTED` on CRITICAL -> `DEGRADED` on HIGH -> `WARNING` on MEDIUM/LOW/WARNING -> `HEALTHY`).
      - `seed_pipeline_runs`: Idempotent upsert of historical execution run records from definitions.
      - `seed_from_scenario_file`: File loader for `pipeline_history.json`.
    - `parse_iso_datetime`: Safe ISO timestamp parsing with UTC timezone normalization.
  - `backend/app/services/pipeline/__init__.py`:
    - Exported `PipelineHistoryService` and `parse_iso_datetime`.
  - `backend/app/services/ingestion/loader.py`:
    - Integrated with `PipelineHistoryService.seed_pipeline_runs` for standardized pipeline run seeding during scenario loading.
  - `backend/app/api/v1/pipelines.py`:
    - `GET /api/v1/pipelines/runs`: Returns historical execution runs with pagination, scenario filtering, and optional log suppression (`include_logs`).
    - `GET /api/v1/pipelines/runs/{run_id}`: Returns single pipeline run detail with step logs and dual-dimension status badges.
  - `backend/app/api/v1/router.py`:
    - Registered `pipelines_router` into master v1 API router.
  - `backend/tests/unit/test_pipeline_service.py`:
    - 8 unit tests verifying ISO parsing, status evaluation across all quality tiers, seed/query operations, and step log parsing with resilient fallback on malformed data.
  - `backend/tests/integration/test_pipeline_api.py`:
    - 8 integration tests asserting empty lists on non-existent scenarios, 3-run sequence for `monday_revenue_mystery`, pagination, and the signature core requirement: the overnight run demonstrates `COMPLETED_SUCCESS` compute status alongside `CORRUPTED` data quality health.
- **Verification Evidence:**
  - `cd backend && pytest tests/unit/test_pipeline_service.py tests/integration/test_pipeline_api.py -v` -> 16 passed in 1.12s.
  - `cd backend && pytest` -> 187 passed in 7.58s (100% unit and integration test suite passing).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 73 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 54 source files.
- **Remaining Limitations:** None. Dual-dimension pipeline run history is persisted and accessible via REST endpoints. Ready for partition freshness & SLA monitoring (`T13`).

### `T13` — Dataset Partition Freshness & SLA Monitoring Service
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/app/schemas/pipeline.py`:
    - `FreshnessStatus` enum (`FRESH`, `STALE`, `MISSING`).
    - `FreshnessCheckResponse` Pydantic model (`dataset_id`, `dataset_name`, `sla_hours`, `expected_partition_timestamp`, `observed_partition_timestamp`, `status`, `hours_behind`, `id`, `scenario_id`, `checked_at`) matching the REST API contract.
  - `backend/app/schemas/__init__.py`:
    - Exported `FreshnessStatus` and `FreshnessCheckResponse`.
  - `backend/app/services/pipeline/freshness.py`:
    - `FreshnessService` engine providing:
      - `calculate_hours_behind`: SLA window calculation preserving exact 2-decimal truncation (yielding 5.99h on Sunday orders 18:00:00 vs 23:59:59).
      - `classify_freshness`: Partition recency classification across `FRESH` (within tolerance / on time), `STALE` (exceeding SLA), and `MISSING` (null/unparseable timestamps).
      - `evaluate_dataset_records` & `evaluate_dataset_file`: In-memory and disk-based partition evaluation directly from CSV/JSON datasets.
      - `get_freshness_status`: Query service fetching persisted `FreshnessCheck` entities with joined `Dataset` names, evaluated delay hours, and filtering by `scenario_id` and `dataset_id`.
      - `seed_freshness_checks`: Idempotent seeding and updating of scenario freshness checkpoints into SQLite.
  - `backend/app/services/pipeline/__init__.py`:
    - Exported `FreshnessService`.
  - `backend/app/services/ingestion/loader.py`:
    - Delegated freshness checkpoint seeding to `FreshnessService.seed_freshness_checks`.
  - `backend/app/api/v1/pipelines.py`:
    - REST endpoint `GET /api/v1/pipelines/freshness` supporting scenario and dataset filters.
  - `backend/tests/unit/test_freshness_service.py`:
    - 7 unit tests covering delay calculation (5.99h), status transitions (`FRESH`, `STALE`, `MISSING`), CSV file evaluation, database seeding, dataset name joins, and null timestamp handling.
  - `backend/tests/integration/test_freshness_api.py`:
    - 5 integration tests asserting:
      - `GET /api/v1/pipelines/freshness` identifies `orders.csv` as `STALE` (5.99 hours behind SLA) on defective `monday_revenue_mystery`.
      - `inventory.csv` identified as `FRESH` (0.0 hours behind).
      - Corrected recovery fixture yields `FRESH` with 0.0 hours behind for all datasets.
      - Dataset filtering by `dataset_id=orders`.
      - Safe handling of missing/null timestamps returning `MISSING` status.
- **Verification Evidence:**
  - `cd backend && pytest tests/unit/test_freshness_service.py tests/integration/test_freshness_api.py -v` -> 12 passed in 1.14s.
  - `cd backend && pytest` -> 199 passed in 11.59s (100% test suite passing, 0 failures).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 76 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 55 source files.
  - `cd frontend && npm test -- --run` -> Vitest 6/6 passed in 765ms (0 frontend regressions).
- **Remaining Limitations:** None. Milestone **M4** is fully completed. The repository is ready for Milestone **M5** (`T14`: Investigation Workspace Engine & Schema Integration) and Milestone **M6** (`T16`: Frontend Navigation Shell, Scenario Switcher & Dataset Inspector).

### `T15` — Safe Report Generator Service (JSON & HTML with CSP)
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/app/schemas/report.py`:
    - Enums & Pydantic models: `ReportFormat` (`json`, `html`), `ReportGenerateRequest`, `ReportGenerateResponse`, `ReportArtifactResponse`, `ReportValidationSummary`, `ReportFindingDetail`, `ReportImpactedAsset`, `ReportPipelineSummary`, and `IncidentReportData`.
    - Strict schemas ensuring reproducible evidence packages with full typing and validation.
  - `backend/app/schemas/__init__.py`:
    - Exported all report models and enums.
  - `backend/app/services/reports/templates/incident_report.html`:
    - Standalone HTML5 template with strict inlined Content Security Policy meta header (`default-src 'none'; style-src 'unsafe-inline'; img-src data:; sandbox;`).
    - Full inlined Lux Purple styling (`#6B46C1` brand primary, `#7C3AED` hover, dark slate backgrounds, high-contrast accessible typography).
    - HTML5 native collapsible `<details class="evidence-panel">` and `<summary>` elements allowing interactive sample keys, line numbers, and sample row inspection with zero client-side JavaScript.
    - Zero external network dependencies, CDNs, or scripts.
  - `backend/app/services/reports/generator.py`:
    - `ReportGeneratorService`:
      - Secure Jinja2 environment configured with `select_autoescape(enabled_extensions=('html', 'xml', 'jinja2'), default_for_string=True, default=True)`.
      - Automatic evidence extraction (`_extract_evidence_samples`) mapping duplicate keys, orphaned foreign keys, line numbers, and sample records.
      - Full data package synthesis connecting Scenario, Investigation, ValidationRun, ValidationFindings, Downstream Blast Radius (via `ImpactAnalysisService`), and Pipeline execution logs.
      - SHA-256 cryptographic integrity hash calculation for all exported artifacts.
      - Artifact file writing to `settings.artifacts_dir` (`data/artifacts/{report_id}.json` and `data/artifacts/{report_id}.html`) and persistence in SQLite `report_artifacts` table.
      - `get_report_artifact`: Retrieval with path traversal protection guaranteeing paths remain within `settings.artifacts_dir`.
      - `list_artifacts`: Filtering and pagination support.
  - `backend/app/services/reports/__init__.py`:
    - Exported `ReportGeneratorService`.
  - `backend/app/api/v1/reports.py`:
    - REST endpoints:
      - `POST /api/v1/reports/generate`: 201 Created report generation endpoint returning download URLs.
      - `GET /api/v1/reports/{id}/export?format=json|html`: 200 OK export streaming endpoint with HTTP CSP headers (`Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; img-src data:; sandbox;`).
      - `GET /api/v1/reports/{id}`: 200 OK inspection endpoint returning both artifact metadata records.
      - `GET /api/v1/reports`: 200 OK query endpoint with scenario and investigation filters.
  - `backend/app/api/v1/router.py`:
    - Registered `reports_router` under prefix `/reports`.
  - `backend/tests/unit/test_report_sanitization.py`:
    - 5 unit tests covering XSS prevention via Jinja2 autoescape (`<script>` and `<img>` tags sanitized to HTML entities), CSP meta header validation, native collapsible details tags, SHA-256 cryptographic calculation, and Unicode/UTF-8 character handling.
  - `backend/tests/integration/test_reports_api.py`:
    - 12 integration tests asserting:
      - `POST /api/v1/reports/generate` generates physical JSON and HTML files and returns 201 Created.
      - `GET /api/v1/reports/{id}/export?format=json` returns structured incident report matching `IncidentReportData` schema.
      - `GET /api/v1/reports/{id}/export?format=html` streams standalone HTML with CSP response headers and inlined styles.
      - Automated evidence synthesis when facts/hypotheses are omitted.
      - Artifact listing and lookup by report ID prefix and scenario.
      - 400 Bad Request on invalid export format.
      - 404 Not Found on nonexistent scenario, validation run, or report artifact.
      - Path traversal attempt rejection (`PATH_TRAVERSAL_DETECTED`).
- **Verification Evidence:**
  - `cd backend && pytest tests/unit/test_report_sanitization.py tests/integration/test_reports_api.py -v` -> 17 passed in 4.08s.
  - `cd backend && pytest` -> 235 passed in 18.67s (100% test suite passing, 0 failures).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 86 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 61 source files.
- **Remaining Limitations:** None. Milestone **M5** (Incident Investigation & Safe Report Generation) is now fully completed. The repository is ready for Milestone **M6** (`T16`: Frontend Navigation Shell, Scenario Switcher & Dataset Inspector).

### `T16` — Frontend Navigation Shell, Scenario Switcher & Dataset Inspector
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `frontend/src/types/`:
    - `scenario.ts`: `ScenarioSummary`, `ScenarioDetail`, `LoadScenarioRequest`, `LoadScenarioResponse`, `FixtureVersion`.
    - `dataset.ts`: `ColumnSchema`, `DatasetResponse`, `DatasetPreviewResponse`, `DatasetUploadResponse`.
    - `common.ts`: `ApiErrorDetail`, `ApiErrorResponse`, `ComputeHealthStatus`, `QualityHealthStatus`, `NavigationTab`.
    - `index.ts`: Re-export domain types.
  - `frontend/src/constants/navigation.ts`:
    - Navigation tab definitions (`Validations`, `Lineage`, `Impact Analysis`, `Pipelines`, `Investigation`, `Recovery`) separated for fast-refresh compliance.
  - `frontend/src/api/`:
    - `client.ts`: Robust typed Fetch wrapper, `ApiClientError` with parsed Lux error envelopes (`error.code`, `error.message`, `error.details`), environment-aware URL resolution (`new URL(path, window.location.origin)`).
    - `scenarios.ts`: `listScenarios`, `getScenario`, and `loadScenario`.
    - `datasets.ts`: `listDatasets`, `getDataset`, `previewDataset`, and `uploadDataset` (multipart FormData).
    - `index.ts`: Unified API exports.
  - `frontend/src/components/common/`:
    - `AlertBanner.tsx`: Accessible dismissible banner (`role="alert"`) with error, warning, success, and info styles.
    - `Modal.tsx`: Accessible dialog wrapper (`role="dialog"`, `aria-modal="true"`) with backdrop dismiss, Escape key listener, and close button.
    - `AppHeader.tsx`: Lux branding (`data-testid="lux-logo"`), active scenario badge (`data-testid="active-scenario"`), ADR-006 dual-dimension health indicator (`data-testid="dual-health-indicator"` separating Compute SUCCESS and Quality CORRUPTED/HEALTHY), datasets drawer toggle, and file upload trigger.
  - `frontend/src/components/scenario/`:
    - `ScenarioSwitcher.tsx`: Scenario selector dropdown, fixture version toggle (`defective` / `corrected`), and "Load Scenario" button with loading spinner state.
  - `frontend/src/components/dataset/`:
    - `DatasetInspector.tsx`: Ingested dataset table displaying filename, format badge (CSV/JSON), formatted row count (e.g. `1,250`), column count, formatted file size (e.g. `102.4 KB`), and per-dataset "Preview" button.
    - `DatasetPreviewModal.tsx`: Paginated dataset row preview modal (`previewDataset`), sticky column header, row index column, previous/next pagination buttons, page indicator, and error state.
    - `UploadModal.tsx`: Drag-and-drop file uploader with client-side format validation (only `.csv` or `.json`), size validation (max 20MB limit enforced), custom dataset display name input, target workspace indicator, and error feedback.
  - `frontend/src/App.tsx`:
    - Central shell orchestration coordinating active tab, scenario switching, fixture reloading, dataset inspection, previewing, and custom dataset ingestion.
  - `frontend/tests/`:
    - `api/client.test.ts`: 5 tests asserting GET/POST/upload execution, standard error envelope parsing, and network failure handling.
    - `components/ScenarioSwitcher.test.tsx`: 5 tests asserting scenario selection, fixture toggling, loading state, and load trigger.
    - `components/DatasetInspector.test.tsx`: 5 tests asserting row count / column count rendering, preview trigger, upload trigger, loading and empty states.
    - `components/DatasetPreviewModal.test.tsx`: 4 tests asserting table columns, pagination next/prev, close trigger, and error handling.
    - `components/UploadModal.test.tsx`: 5 tests asserting dropzone rendering, non-CSV/JSON format rejection, >20MB limit rejection, valid upload submission, and API failure alert.
    - `App.test.tsx`: 10 integration tests asserting header branding, active scenario badge, dual-health indicator, tab switching, dataset table row counts, scenario loading trigger, dataset inspector toggle, and upload modal opening.
- **Verification Evidence:**
  - `cd frontend && npm run typecheck` (`tsc --noEmit`) -> 0 errors.
  - `cd frontend && npm run lint` (`eslint .`) -> 0 warnings, 0 errors.
  - `cd frontend && npm test` (`vitest run`) -> 34 passed across 6 test files in 7.81s.
  - `cd frontend && npm run build` (`tsc && vite build`) -> Built production assets in `frontend/dist/` in 7.56s (HTML 1.01 kB, CSS 22.94 kB, JS 186.84 kB).
  - `cd backend && pytest` -> 235 passed in 17.99s (no regressions).
- **Remaining Limitations:** None. Frontend foundation, navigation, scenario switcher, and dataset inspector are fully operational. Ready for `T17` (Quality Validation Findings Explorer & Evidence Drawer UI).

### `T17` — Quality Validation Findings Explorer & Evidence Drawer UI
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `frontend/src/types/`:
    - `validation.ts`: TypeScript models matching backend schemas: `RuleCategory`, `RuleSeverity`, `RuleStatus`, `ValidationRunResponse`, `DuplicateRowEvidence`, `ViolationRowEvidence`, `FindingEvidence`, `ValidationFindingItem`, `ValidationFindingsListResponse`, and `ValidationFilterParams`.
    - `index.ts`: Re-export all validation types.
  - `frontend/src/api/`:
    - `validations.ts`: Typed REST API client:
      - `executeValidationRun(scenarioId, datasetIds?)`: Dispatches `POST /api/v1/validations/run`.
      - `getValidationRun(runId)`: Fetches `GET /api/v1/validations/runs/{run_id}`.
      - `listValidationRuns(scenarioId?, limit?, offset?)`: Fetches `GET /api/v1/validations/runs`.
      - `listValidationFindings(runId, options?)`: Fetches `GET /api/v1/validations/runs/{run_id}/findings` with server-side query filters.
    - `index.ts`: Re-export validations API functions.
  - `frontend/src/components/validation/`:
    - `ValidationSummaryCards.tsx`: Top meta bar (Run ID, active fixture version, run status badge, execution timestamp) and 5 KPI cards (Total Checks, Passed Checks with emerald theme, Failed Checks with rose theme, Warnings with amber theme, and Execution Duration in milliseconds).
    - `FindingsTable.tsx`: Filterable findings explorer supporting:
      - Severity filter (`ALL`, `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`).
      - Status filter (`ALL`, `FAILED`, `WARNING`, `PASSED`).
      - Dataset filter (`ALL` or specific datasets).
      - Live search input matching Rule ID, Name, Dataset, and issue diagnosis.
      - Sorting by severity, status, dataset, and affected records.
      - Per-row "View Evidence" trigger and "Trace Impact" action button with event propagation isolation.
    - `EvidenceDrawer.tsx`: Accessible slide-over drawer (`role="dialog"`, `aria-modal="true"`) featuring:
      - Keyboard focus trapping (`Tab` and `Shift+Tab`) and `Escape` key close listener.
      - Rule header with severity, status, and category badges.
      - "Observed vs Expected" comparative card detailing specific constraint deviations.
      - Structured sample records breakdown:
        - Duplicate key groupings with occurrences and 1-indexed line numbers (`#43, #109`).
        - Sample orphaned foreign keys and broken reference rows (`order_items` referencing non-existent `PRD-9001`).
        - Negative quantity and range violations.
        - Temporal ingestion gap metrics (`max_gap_hours`, `gap_start`, `gap_end`).
        - Raw JSON diagnostic collapsible panel (`<details>`).
      - "Trace Downstream Impact" action button delegating to lineage/impact explorer.
    - `ValidationView.tsx`: Orchestration view connecting summary cards, execution trigger button ("Execute Quality Validations" / "Re-run Quality Validations"), error alert banner, empty state, findings table, and slide-over evidence drawer.
    - `index.ts`: Unified validation component exports.
  - `frontend/src/App.tsx`:
    - Mounted `ValidationView` within the default `validations` tab panel, wiring "Trace Impact" to automatically transition to the `impact` tab with alert context.
  - `frontend/tests/`:
    - `api/validations.test.ts`: 4 unit tests verifying GET/POST execution, query parameter serialisation, and response typing.
    - `components/ValidationSummaryCards.test.tsx`: 4 component tests verifying rendering, metric counts, run status badges, and loading states.
    - `components/FindingsTable.test.tsx`: 8 component tests verifying table rendering, `CRITICAL` severity isolation of duplicate order checks (`VAL-ORD-001`), status/dataset filtering, search query filtering, row selection, Trace Impact click isolation, and filter reset.
    - `components/EvidenceDrawer.test.tsx`: 8 component tests verifying closed/null state, observed vs expected values, sample duplicates with line numbers, orphaned keys, backdrop/close/Escape dismissal, and Trace Impact trigger.
    - `components/ValidationView.test.tsx`: 4 integration tests verifying empty state, run execution trigger, summary cards display, and evidence drawer invocation.
    - `App.test.tsx`: 10 integration tests verified passing with validations tab integration.
- **Verification Evidence:**
  - `cd frontend && npm test -- --run` (`vitest run`) -> 62 passed across 11 test files in 9.43s (100% pass rate).
  - `cd frontend && npm run typecheck` (`tsc --noEmit`) -> 0 errors.
  - `cd frontend && npm run lint` (`eslint .`) -> 0 warnings, 0 errors.
  - `cd frontend && npm run build` (`tsc && vite build`) -> Built production bundle in 6.90s (HTML 1.01 kB, CSS 28.08 kB, JS 229.35 kB).
  - `cd backend && pytest` -> 235 passed across 19 test files in 16.99s (zero backend regressions).
- **Remaining Limitations:** None. Findings Explorer and Evidence Drawer UI are fully operational with zero mocks and authentic API integration. Ready for `T18` (Interactive Lineage DAG & Blast Radius Visualization UI).

### `T18` — Interactive Lineage DAG & Blast Radius Visualization UI
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - Installed `@xyflow/react` (`^12.12.0`) in `frontend/package.json`.
  - `frontend/src/types/`:
    - `lineage.ts`: TypeScript models matching backend schemas: `LineageNodeType`, `NodePosition`, `LineageNodeData`, `LineageNode`, `LineageEdge`, `LineageGraphResponse`, `LineageNodeSummary`, and `LineageNodeDetail`.
    - `impact.ts`: TypeScript models matching backend impact schemas: `AssetImpactStatus` (`CONFIRMED_FAILED`, `DIRECTLY_AFFECTED`, `POTENTIALLY_AFFECTED`, `HEALTHY`), `ImpactTargetType`, `AffectedAsset`, `ImpactSummary`, `BlastRadiusReport`, and `ImpactTraceRequest`.
    - `index.ts`: Re-export all lineage and impact domain types.
  - `frontend/src/api/`:
    - `lineage.ts`: Typed REST API client:
      - `getLineageGraph(scenarioId?)`: Fetches `GET /api/v1/lineage` with Dagre-computed node coordinates.
      - `getLineageNodeDetail(nodeId, scenarioId?)`: Fetches `GET /api/v1/lineage/nodes/{id}` with immediate predecessors and successors.
      - `traceDownstreamImpact(request)`: Dispatches `POST /api/v1/impact/trace` with full blast radius computation.
    - `index.ts`: Re-export lineage API client methods.
  - `frontend/tests/setup.ts`:
    - Added mocks for `ResizeObserver`, `DOMMatrixReadOnly`, and `SVGElement.prototype.getBBox` enabling React Flow component testing in jsdom.
  - `frontend/src/components/lineage/`:
    - `CustomNode.tsx`: Custom React Flow node component implementing:
      - Asset type styling for all 5 classifications: `SOURCE_DATASET` (Blue, Database), `TRANSFORMATION` (Amber, Cpu), `DERIVED_DATASET` (Indigo, Layers), `METRIC` (Emerald, TrendingUp), and `REPORT` (Fuchsia, LayoutDashboard).
      - Dual-dimension status chips: Compute Status (terminal icon + "Exit 0" or "Failed") and Quality Health (badge + "Healthy", "Corrupted", or "Degraded").
      - Blast radius status chips: "Failure Origin" (`CONFIRMED_FAILED`), "Direct Consumer" (`DIRECTLY_AFFECTED`), and "Blast Radius" (`POTENTIALLY_AFFECTED`).
      - Visual states: selected glow ring (`ring-lux-400`), failure origin red glow (`ring-rose-500`), and dimmed state (`opacity-30`) for assets outside active blast radius.
      - Left target and right source connection handles.
    - `LineageLegend.tsx`: Visual reference card explaining node types, dual health status dimensions (ADR-006), and blast radius classification tiers.
    - `NodeDetailsPanel.tsx`: Slide-over inspector panel displaying:
      - Node metadata (owner, description, storage dataset, engine).
      - Dual-dimension status cards (Compute vs Quality).
      - Blast radius summary with total affected assets, breakdown by tier, and step-by-step dependency chain explanations.
      - Immediate upstream predecessors and downstream consumers with clickable navigation.
      - "Center Node" and "Close" action triggers.
    - `LineageView.tsx`: Main interactive React Flow canvas container managing:
      - Toolbar: Node and edge counts, live search input, asset type filter dropdown, "Reset Highlight" button, and Legend toggle.
      - React Flow canvas: Zoom, pan, background grid dots, interactive Controls, and custom-colored MiniMap.
      - Interactive path highlighting: clicking a node traces its downstream blast radius via `POST /api/v1/impact/trace`, highlighting affected nodes and animating edges in rose/red while dimming unrelated graph branches.
      - Slide-over `NodeDetailsPanel` for inspecting selected nodes.
    - `index.ts`: Unified lineage component exports.
  - `frontend/src/App.tsx`:
    - Mounted `LineageView` in both `lineage` and `impact` tabs.
    - Connected "Trace Impact" from `ValidationView` findings to automatically transition to Lineage with the failing target pre-selected and highlighted.
  - `frontend/tests/`:
    - `api/lineage.test.ts`: 3 unit tests verifying graph retrieval, node details, and impact trace API calls.
    - `components/CustomNode.test.tsx`: 7 component tests verifying node type rendering, dual status chips (Exit 0 vs Corrupted), blast radius chips, and dimmed states.
    - `components/NodeDetailsPanel.test.tsx`: 5 component tests verifying metadata, dual health cards, blast radius summary, dependency path breadcrumbs, node selection, and panel close.
    - `components/LineageView.test.tsx`: 6 component tests asserting:
      - Acceptance Criterion 1: renders all 16 nodes with clear visual hierarchy.
      - Acceptance Criterion 2: selecting `src_orders` highlights downstream path through to `report_exec_dash`.
      - Search query filtering.
      - Asset type dropdown filtering.
      - Reset Highlight button restoring default un-dimmed graph.
      - Network failure error boundary state.
    - `App.test.tsx`: Updated with lineage API mocks and verified tab switching to Lineage DAG visualizer.
- **Verification Evidence:**
  - `cd frontend && npm test -- --run` (`vitest run`) -> 83 passed across 15 test files in 17.49s (100% pass rate).
  - `cd frontend && npm run typecheck` (`tsc --noEmit`) -> 0 errors.
  - `cd frontend && npm run lint` (`eslint .`) -> 0 warnings, 0 errors.
  - `cd frontend && npm run build` (`tsc && vite build`) -> Built production bundle in 9.55s (HTML 1.01 kB, CSS 54.60 kB, JS 451.95 kB / gzip 133.83 kB).
  - `cd backend && pytest` -> 235 passed across 19 test files in 18.15s (zero regressions).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 86 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 61 source files.
- **Remaining Limitations:** None. Interactive Lineage DAG and Blast Radius visualizer is fully implemented and tested with authentic graph data and traversal. Ready for `T19` (Pipeline Observability, Freshness & Run History UI).

### `T19` — Pipeline Observability, Freshness & Run History UI
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `frontend/src/types/pipeline.ts`:
    - Domain types for `PipelineExecutionStatus`, `FreshnessStatus`, `PipelineStepLog`, `PipelineRun`, and `FreshnessCheck`.
    - Integrated with `QualityHealthStatus` in `frontend/src/types/common.ts` and re-exported in `frontend/src/types/index.ts`.
  - `frontend/src/api/pipelines.ts`:
    - `listPipelineRuns`: Fetches historical runs with duration, record counts, step logs, and dual-dimension status.
    - `getPipelineRun`: Fetches detailed metrics and step logs for an individual run ID.
    - `getPipelineFreshness`: Fetches partition freshness checkpoints comparing expected SLA cutoffs against observed partition timestamps.
    - Exported via `frontend/src/api/index.ts`.
  - `frontend/src/components/pipeline/DualStatusCallout.tsx`:
    - Prominent ADR-006 visual callout: *"Execution Succeeded (Exit 0) but Data Quality is Corrupted"*.
    - Explicitly surfaces the compute vs quality health divergence (`COMPLETED_SUCCESS` exit 0 badge alongside `CORRUPTED` data health badge).
    - Summarizes the introduced defects (15 duplicate orders, 24 orphaned items, 5.99h Sunday ingestion gap) with quick actions to view step logs or trace blast radius in Lineage.
  - `frontend/src/components/pipeline/PipelineHistoryTimeline.tsx`:
    - Summary metrics cards (historical run count, compute success rate 100%, healthy runs count, corrupted runs count).
    - Chronological run cards with relative duration bar charts comparing execution times.
    - Interactive collapsible step logs table displaying step names (`extract_sources`, `transform_clean_orders`, `transform_order_line_items`, `aggregate_daily_revenue`), success status badges, record counts, and execution duration in milliseconds/seconds with proportional share bars.
  - `frontend/src/components/pipeline/FreshnessView.tsx`:
    - Partition freshness overview metrics (monitored partitions, SLA compliant, stale/breached, max lag).
    - Status cards for dataset partitions (`orders.csv`, `inventory.csv`) displaying configured SLA hours (24h, 6h), expected cutoff timestamp, observed partition max timestamp, and evaluation time.
    - Highlights SLA breaches with prominent staleness warning box (e.g. `orders.csv` is 5.99 hours behind schedule).
  - `frontend/src/components/pipeline/PipelineObservabilityView.tsx`:
    - Container view coordinating sub-navigation tabs ("All Observability", "Run History", "Partition Freshness").
    - Synchronizes runs and freshness data with loading spinners, refresh trigger, and error handling.
  - `frontend/src/App.tsx`:
    - Mounted `PipelineObservabilityView` in the `pipelines` tab with seamless integration into the active scenario.
    - Connected "Trace Blast Radius" from the dual-dimension anomaly callout to automatically navigate to the Lineage tab with `src_orders` highlighted.
  - `frontend/tests/`:
    - `tests/api/pipelines.test.ts`: 3 unit tests verifying runs listing, single run retrieval, and freshness check API calls.
    - `tests/components/DualStatusCallout.test.tsx`: 5 component tests verifying callout text, dual-dimension badges, button callbacks, and dismissal for healthy runs.
    - `tests/components/PipelineHistoryTimeline.test.tsx`: 6 component tests verifying summary cards, step logs expansion/collapse, empty states, and Acceptance Criterion 1 (rendering overnight run with `SUCCESS` compute badge alongside `CORRUPTED` data health badge).
    - `tests/components/FreshnessView.test.tsx`: 7 component tests verifying Acceptance Criterion 2 (`orders.csv` partition staleness with 5.99 hours behind SLA), configured SLA hours, timestamps, compliant inventory partition, and refresh action.
    - `tests/components/PipelineObservabilityView.test.tsx`: 4 component tests verifying data synchronization, sub-tab switching, refresh refetching, and API error states.
    - `tests/App.test.tsx`: Verified semantic navigation tab switching to the Pipelines workspace.
- **Verification Evidence:**
  - `cd frontend && npm test -- --run` (`vitest run`) -> 108 passed across 20 test files in 15.01s (100% pass rate).
  - `cd frontend && npm run typecheck` (`tsc --noEmit`) -> 0 errors.
  - `cd frontend && npm run lint` (`eslint .`) -> 0 warnings, 0 errors.
  - `cd frontend && npm run build` (`tsc && vite build`) -> Built production bundle in 8.43s (HTML 1.01 kB, CSS 58.36 kB, JS 480.13 kB / gzip 138.86 kB).
  - `cd backend && pytest` -> 235 passed across 19 test files in 16.31s (zero regressions).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 86 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 61 source files.
- **Remaining Limitations:** None. Pipeline observability, dual-dimension status tracking, and partition freshness monitoring views are fully operational and verified. Ready for `T20` (Investigation Workspace & Report Export Modal UI).

### `T20` — Investigation Workspace & Report Export Modal UI
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `frontend/src/api/client.ts`:
    - Added `apiPatch`, `apiDelete`, and `apiGetText` methods with typed error handling and response unwrapping.
  - `frontend/src/types/investigation.ts`:
    - Domain types for `InvestigationStatus`, `InvestigationItemType`, `InvestigationItem`, `InvestigationResponse`, `InvestigationCreateRequest`, `InvestigationUpdateRequest`, and `InvestigationSynthesizeRequest`.
  - `frontend/src/types/report.ts`:
    - Domain types for `ReportFormat`, `ReportGenerateRequest`, `ReportGenerateResponse`, and `ReportArtifactResponse`.
  - `frontend/src/api/investigations.ts`:
    - `listInvestigations`: List workspaces by scenario and status.
    - `getInvestigation`: Fetch workspace by ID.
    - `createInvestigation`: Create workspace with facts, hypotheses, and action items.
    - `updateInvestigation`: Patch title, status, facts, hypotheses, and action items.
    - `deleteInvestigation`: Delete workspace by ID.
    - `synthesizeInvestigation`: Synthesizes workspace automatically from validation findings, pipeline runs, and lineage blast radius.
  - `frontend/src/api/reports.ts`:
    - `generateReport`: Generate immutable JSON and safe styled standalone HTML incident reports.
    - `exportReportArtifact`: Retrieve raw HTML or JSON report artifact content.
    - `getReportArtifacts`: Retrieve metadata records for generated report artifacts.
    - `listReportArtifacts`: List persisted report artifacts by scenario and investigation.
  - `frontend/src/components/reports/download.ts`:
    - Safe browser file download utility (`downloadFile`) creating a Blob URL and guaranteeing memory cleanup via `URL.revokeObjectURL(url)`.
  - `frontend/src/components/reports/InvestigationWorkspace.tsx`:
    - Enforces FR-06 and ADR-005 fact-hypothesis boundary separation across 3 dedicated architectural zones:
      1. Confirmed Observations (Verified Facts) with ground-truth evidence cards, fact addition, and removal.
      2. Working Hypotheses (Theories) with root-cause candidate tracking, addition, and removal.
      3. Remediation Checklist (Action Items) with interactive completion toggles, addition, and removal.
    - Quick metrics bar displaying verified facts count, hypotheses count, and action items completion ratio.
    - Status pill dropdown (`OPEN`, `INVESTIGATING`, `RESOLVED`, `RECOVERED`, `CLOSED`).
    - One-click "Synthesize Evidence" action automatically assembling workspace state from scenario validation runs, findings, and pipeline status.
    - Direct cross-workspace jump links to "Inspect Lineage DAG" and "Inspect Quality Findings".
  - `frontend/src/components/reports/ReportModal.tsx`:
    - Report generation modal with title customization and pre-flight item count checks.
    - In-app tabbed preview:
      1. HTML Preview: Standalone sanitized HTML rendered inside a secure `<iframe>` (`sandbox="allow-same-origin"`).
      2. JSON Artifact: Monospace formatted code block with syntax display and one-click "Copy JSON" action with clipboard feedback.
    - Direct download actions for `.html` and `.json` artifacts invoking `downloadFile` with automatic blob URL revocation to prevent memory leaks.
    - Direct browser download URL links matching API contract endpoints (`/api/v1/reports/{id}/export?format=html`).
  - `frontend/src/App.tsx`:
    - Mounted `InvestigationWorkspace` in the `investigation` tab with scenario routing and cross-tab navigation callbacks.
  - `frontend/tests/`:
    - `tests/api/investigations.test.ts`: 6 unit tests verifying list, get, create, update, delete, and synthesize API calls.
    - `tests/api/reports.test.ts`: 4 unit tests verifying generate, export artifact text, get artifacts, and list artifacts.
    - `tests/components/InvestigationWorkspace.test.tsx`: 6 component tests verifying empty state synthesis, 3-zone boundary separation, item additions/removals/toggles, workspace persistence, and ReportModal opening.
    - `tests/components/ReportModal.test.tsx`: 5 component tests verifying report generation, HTML iframe preview, JSON artifact preview, Acceptance Criterion 1 (user can generate report and download both HTML and JSON), Acceptance Criterion 2 (HTML structure has full CSS styles, CSP headers, and valid HTML5), and error state handling.
    - `tests/App.test.tsx`: Verified navigation tab switching to the Investigation workspace.
- **Verification Evidence:**
  - `cd frontend && npm test -- --run` (`vitest run`) -> 128 passed across 24 test files in 18.31s (100% pass rate).
  - `cd frontend && npm run typecheck` (`tsc --noEmit`) -> 0 errors.
  - `cd frontend && npm run lint` (`eslint .`) -> 0 warnings, 0 errors.
  - `cd frontend && npm run build` (`tsc && vite build`) -> Built production bundle in 9.84s (HTML 1.01 kB, CSS 61.34 kB, JS 514.83 kB / gzip 145.14 kB).
  - `cd backend && pytest` -> 235 passed across 19 test files in 16.75s (zero regressions).
- **Remaining Limitations:** None. Investigation workspace, fact-hypothesis boundary separation, and incident report generation modal with HTML/JSON preview and downloads are fully operational and verified. Milestone **M6** is `COMPLETED`. Ready for `T21` (Recovery Verification Backend Engine).

### `T21` — Recovery Verification Backend Engine
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/app/schemas/recovery.py`:
    - `RecoveryRunSummary`: Captures run metrics (`run_id`, `fixture_version`, `failed_checks`, `quality_health`, total/passed checks, duration, and timestamp).
    - `ResolvedFindingItem`: Individual finding resolution status (`RESOLVED` vs `UNRESOLVED`, severity, category, dataset ID, previous status, current status, and message).
    - `RecoveryComparison`: Full before-and-after comparison envelope (`previous_run`, `current_run`, `resolved_findings`, `downstream_recovery_status`).
    - `RecoveryVerifyRequest` and `RecoveryVerifyResponse`: Input and output schemas matching Section 8 of `api-contracts.md`.
  - `backend/app/schemas/__init__.py`:
    - Exported all recovery schema models.
  - `backend/app/services/validation/recovery.py` (`RecoveryService`):
    - `swap_fixtures`: Safely updates scenario dataset file paths, file sizes, record counts, and schema definitions to clean `corrected/` fixtures without destroying prior validation runs or findings history. Reloads `PipelineRun` and `FreshnessCheck` records from `corrected/pipeline_history.json`.
    - `verify_recovery`: Orchestrates baseline run resolution, clean fixture swapping, validation re-execution, before-and-after diff calculation, and downstream Lineage DAG health assessment.
    - Resolves all 4 defective checks (`VAL-ORD-001`, `VAL-ORD-002`, `VAL-INV-001`, `VAL-FRESH-001`) from `FAILED` to `RESOLVED`.
    - Verifies that zero failed root nodes causes all Lineage DAG nodes to transition to `HEALTHY`, yielding `downstream_recovery_status="ALL_ASSETS_HEALTHY"`.
    - Accurately reports `PARTIALLY_RECOVERED` when simulated with partial fixes.
  - `backend/app/api/v1/recovery.py` & `backend/app/api/v1/router.py`:
    - Exposes `POST /api/v1/recovery/verify` endpoint with dependency injection and error handling.
  - `backend/tests/integration/test_recovery_api.py`:
    - 4 integration tests verifying acceptance criteria, automatic baseline run execution when validation was not run prior to recovery, lineage and freshness updates, and 404 on unknown scenarios.
  - `backend/tests/unit/test_recovery_service.py`:
    - 5 unit tests verifying invalid fixture version handling, missing scenario handling, live service swapping and recovery verification, and partial recovery edge cases.
- **Verification Evidence:**
  - `cd backend && pytest tests/integration/test_recovery_api.py tests/unit/test_recovery_service.py` -> 9 passed in 1.49s.
  - `cd backend && pytest tests/integration/test_recovery_api.py` -> 4 passed in 0.90s.
  - `cd backend && pytest` -> 245 passed across 21 test files in 14.82s (zero regressions).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 91 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 64 source files.
  - `cd frontend && npm run typecheck && npm run lint && npm test -- --run` -> Vitest 132 passed across 24 test files; `tsc` and `eslint` 0 errors.
- **Remaining Limitations:** None. Backend recovery verification engine is fully operational, thoroughly tested, and ready for frontend integration in `T22`.

### `T22` — Recovery Verification Frontend View
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `frontend/src/types/recovery.ts`:
    - `RecoveryRunSummary`: Run metrics (`run_id`, `fixture_version`, `failed_checks`, `quality_health`, `total_checks`, `passed_checks`, `execution_duration_ms`, `executed_at`).
    - `ResolvedFindingItem`: Individual finding resolution status (`RESOLVED` vs `UNRESOLVED`, severity, category, dataset ID, before status, after status, diagnostic message).
    - `RecoveryComparison`: Full before-and-after comparison envelope (`previous_run`, `current_run`, `resolved_findings`, `downstream_recovery_status`).
    - `RecoveryVerifyRequest` and `RecoveryVerifyResponse`.
  - `frontend/src/types/index.ts`:
    - Exported all recovery type definitions.
  - `frontend/src/api/recovery.ts`:
    - Implemented `verifyRecovery(scenarioId, targetFixtureVersion = 'corrected')` dispatching `POST /api/v1/recovery/verify`.
  - `frontend/src/api/index.ts`:
    - Exported recovery API methods.
  - `frontend/src/components/recovery/DownstreamRecoveryBanner.tsx`:
    - Trust restoration banner for `ALL_ASSETS_HEALTHY` (`ShieldCheck`, "Downstream Trust Restored: All Lineage Assets Healthy", confirming derived tables, metrics, and Executive Monday Dashboard integrity) with quick action to navigate to the Lineage DAG.
    - Handles `PARTIALLY_RECOVERED` (amber warning) and `RECOVERY_FAILED` (rose corruption) states.
  - `frontend/src/components/recovery/ComparisonMetricCards.tsx`:
    - Side-by-side run cards comparing Before Recovery (Defective, `CORRUPTED`, 4 failed) vs After Recovery (Clean, `HEALTHY`, 0 failed) with run IDs, timestamps, execution durations, and resolution delta (+6ms performance, 4 checks resolved).
  - `frontend/src/components/recovery/ResolvedChecksList.tsx`:
    - Checklist of evaluated quality checks with green `RESOLVED` badges (`CheckCircle2`), transition chips (`FAILED` → `PASSED`), rule IDs, names, dataset tags, severity chips, and resolution percentage (4 of 4 Resolved, 100%).
    - Includes interactive filter pills (`All (4)`, `Resolved (4)`, `Unresolved (0)`).
  - `frontend/src/components/recovery/RecoveryDiffView.tsx`:
    - Complete view orchestrating the recovery workflow: initial onboarding state with defect summary and primary CTA button, loading spinner state during re-execution, error alert handling, comparison results, and cross-workspace navigation links to inspect clean validations and restored lineage.
  - `frontend/src/components/recovery/index.ts`:
    - Barrel export for all recovery UI components.
  - `frontend/src/App.tsx`:
    - Mounted `RecoveryDiffView` into the `recovery` tab, updating scenario fixture state to `corrected` upon successful verification and raising a global success alert.
  - Test Suite Deliverables:
    - `frontend/tests/api/recovery.test.ts`: Unit tests for `verifyRecovery` client.
    - `frontend/tests/components/DownstreamRecoveryBanner.test.tsx`: Tests for all 3 health states and lineage navigation.
    - `frontend/tests/components/ComparisonMetricCards.test.tsx`: Tests for side-by-side metrics and delta calculations.
    - `frontend/tests/components/ResolvedChecksList.test.tsx`: Tests for 100% resolution checklist, checkmarks, and filters.
    - `frontend/tests/components/RecoveryDiffView.test.tsx`: Tests for initial callout, verify CTA trigger, before-and-after diff rendering, re-verify button, error alerts, and cross-tab navigation.
    - `frontend/tests/App.test.tsx`: End-to-end component test verifying tab switching to Recovery and executing recovery verification.
- **Verification Evidence:**
  - `cd frontend && npm test -- --run` (`vitest run`) -> 145 passed across 29 test files in 20.96s (100% pass rate).
  - `cd frontend && npm run typecheck` (`tsc --noEmit`) -> 0 errors.
  - `cd frontend && npm run lint` (`eslint .`) -> 0 warnings, 0 errors.
  - `cd frontend && npm run build` (`tsc && vite build`) -> Production build successful in 8.13s (HTML 1.01 kB, CSS 67.50 kB, JS 545.45 kB / gzip 150.21 kB).
  - `cd backend && pytest` -> 245 passed across 21 test files in 19.16s (zero regressions).
- **Remaining Limitations:** None. Recovery Verification view is fully functional, styled with Lux Purple and accessible tokens, and verified against all acceptance criteria. Ready for `T23` (Signature Scenario End-to-End Test Suite).

### `T23` — Signature Scenario End-to-End Test Suite
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `backend/tests/scenarios/test_monday_revenue_mystery.py`:
    - Comprehensive scenario acceptance test suite covering the entire 8-step "Trace the Failure" workflow for *Monday Revenue Mystery*.
    - `test_monday_revenue_mystery_full_trace_the_failure_e2e`: Continuous end-to-end master test traversing the entire incident lifecycle in a single deterministic test session:
      1. **Stage 1 (Ingestion):** Ingests defective scenario fixtures, verifying 4 loaded datasets (`orders`, `order_items`, `products`, `inventory`), 5,170 total records (1,250 orders, 3,420 items, 250 products, 250 inventory), 8 registered rules, and 16 DAG nodes.
      2. **Stage 2 (Validation):** Executes validation engine, asserting `FAILED` status, 4 passed checks, 4 failed checks, and `CORRUPTED` quality health.
      3. **Stage 3 (Evidence):** Asserts exact record counts and structured diagnostic evidence: 15 duplicate orders (`VAL-ORD-001`, `CRITICAL`), 24 broken foreign keys (`VAL-ORD-002`, `HIGH`), 8 negative stock quantities (`VAL-INV-001`, `HIGH`), and 1 temporal gap (`VAL-FRESH-001`, `MEDIUM`, max_gap_hours >= 4.0h). Verifies combined filter `severity=CRITICAL&status=FAILED` isolates `VAL-ORD-001`.
      4. **Stage 4 (Lineage):** Asserts 16 nodes and 14 edges with Dagre layout `(x, y)` coordinates, acyclicity (`is_dag=True`, 0 cycles, 0 dangling edges), and upstream lineage ancestors of `report_exec_dash` (orders, items, products).
      5. **Stage 5 (Impact):** Asserts downstream blast radius from `orders.csv` propagates through `dim_orders` (`DIRECTLY_AFFECTED`) to `agg_daily_revenue`, `metric_revenue`, and `report_exec_dash` (`POTENTIALLY_AFFECTED`) with full dependency paths and explanations. Asserts `src_inventory` blast radius isolates stock alerts and does not impact executive revenue dashboards.
      6. **Stage 6 (Pipeline History):** Asserts dual-dimension tracking for the overnight ETL run (`pipe_run_20261020_0200`) with compute execution status `COMPLETED_SUCCESS` (exit 0) alongside data quality health `CORRUPTED`. Verifies `orders.csv` partition staleness (>0h behind SLA).
      7. **Stage 7 (Reporting):** Synthesizes investigation workspace, generates immutable JSON and HTML report artifacts with physical files in `settings.artifacts_dir`, asserts CSP security headers (`default-src 'none'`, `style-src 'unsafe-inline'`, `sandbox`), auto-escaping, inlined CSS, no external `<script>`/`<link>` tags, and full report audit summary (8 total evaluated findings, 4 failed).
      8. **Stage 8 (Recovery):** Triggers recovery verification, asserting transition from `CORRUPTED` to `HEALTHY`, 0 failed checks, all 4 defects `RESOLVED` (`FAILED` → `PASSED`), `ALL_ASSETS_HEALTHY` downstream recovery status, all 16 lineage DAG nodes restored to `HEALTHY`, freshness restored to `FRESH` (0.0h behind), and preservation of historical runs.
    - Modular isolation tests for each of the 8 stages:
      - `test_stage_1_scenario_ingestion_and_dataset_counts`
      - `test_stage_2_quality_validations_execution`
      - `test_stage_3_structured_row_evidence_and_capping`
      - `test_stage_4_lineage_dag_integrity_and_traversal`
      - `test_stage_5_downstream_impact_blast_radius_and_isolation`
      - `test_stage_6_pipeline_observability_and_dual_dimension`
      - `test_stage_7_investigation_and_safe_report_exports`
      - `test_stage_8_recovery_verification_and_trust_restoration`
- **Verification Evidence:**
  - `cd backend && pytest tests/scenarios/test_monday_revenue_mystery.py::test_monday_revenue_mystery_full_trace_the_failure_e2e` -> 1 passed in 1.13s (exceeds < 2.0s acceptance criteria).
  - `cd backend && pytest -v tests/scenarios/test_monday_revenue_mystery.py` -> 9 passed in 3.27s (100% assertions passed across all 8 workflow stages).
  - `cd backend && pytest` -> 254 passed across 22 test files in 21.89s (zero regressions).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 92 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 64 source files.
  - `cd frontend && npm run typecheck && npm run lint && npm test -- --run` -> `tsc` 0 errors, `eslint` 0 errors, `vitest` 145 passed across 29 test files in 15.39s.
- **Remaining Limitations:** None. Entire 8-step "Trace the Failure" end-to-end workflow is fully automated, verified, and passing under 2 seconds. Ready for Milestone M8: `T24` (Docker Compose Orchestration & Production Polish).

### `T24` — Docker Compose Orchestration, Production Build & Operational Documentation
- **Status:** `COMPLETED`
- **Key Deliverables:**
  - `.dockerignore`: Root exclusion configuration ignoring `node_modules/`, `dist/`, `.venv/`, `__pycache__/`, test caches, and ephemeral SQLite database/upload/artifact files while preserving bundled scenarios in `data/scenarios/`.
  - `backend/Dockerfile`: Multi-stage container build based on `python:3.13-slim`:
    - Stage 1 (`builder`): Compiles dependencies into isolated `/opt/venv` using `pip install --no-cache-dir .`.
    - Stage 2 (`runtime`): Creates dedicated non-root user `lux` (UID 1000), copies `/opt/venv`, sets `LUX_DATA_DIR=/app/data` and `LUX_ENV=production`, seeds bundled scenarios, verifies directory permissions, defines native container healthcheck (`/health`), and serves with `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
  - `frontend/nginx.conf`: Production Nginx configuration listening on port 3000:
    - Gzip compression with `gzip_vary on` and standard MIME types.
    - Security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`).
    - Reverse proxy location `/api/` forwarding to `http://backend:8000` with streaming headers and `client_max_body_size 25M` to accommodate 20MB file uploads.
    - Root health check proxy location `/health` forwarding to `http://backend:8000/health`.
    - Single Page Application HTML5 history fallback (`try_files $uri $uri/ /index.html`).
    - 1-year caching for immutable static assets.
  - `frontend/Dockerfile`: Multi-stage container build:
    - Stage 1 (`builder`): Based on `node:22-alpine`, installs locked dependencies via `npm ci`, and compiles optimized production assets via `npm run build`.
    - Stage 2 (`runtime`): Based on `nginx:alpine`, copies `nginx.conf` and compiled static assets to `/usr/share/nginx/html`, exposes port 3000, and verifies health via `wget -qO- http://127.0.0.1:3000/`.
  - `docker-compose.yml`: Local multi-container orchestration specification:
    - Declares `backend` (port 8000) and `frontend` (port 3000) services on dedicated `lux-network` bridge.
    - Configures persistent host volume mount `./data:/app/data` for SQLite database and report artifacts.
    - Declares startup dependency with `depends_on: { backend: { condition: service_healthy } }`.
    - Enforces container resource quotas (`1.0` CPU and `1024M` RAM for backend; `1.0` CPU and `512M` RAM for frontend) per security specifications.
  - `README.md`: Complete overhaul and operational quickstart guide:
    - Architecture diagrams (Mermaid flowchart and ASCII workflow).
    - 8-stage "Trace the Failure" investigation walkthrough.
    - Full *Monday Revenue Mystery* incident briefing, injected defect taxonomy, and blast radius breakdown.
    - Dual quickstart instructions: Option A (One-command Docker Compose stack `docker compose up --build`) and Option B (Local Python 3.13 + Node 22 setup).
    - Complete test verification commands for Pytest, Vitest, Ruff, Mypy, ESLint, and Vite.
    - Security and trust boundary documentation (XSS auto-escaping, CSP headers, upload limits, SQLite WAL mode).
    - Repository directory layout tree.
- **Verification Evidence:**
  - `docker compose build` -> Succeeded with 0 errors; built `lux-data-observability-backend:latest` and `lux-data-observability-frontend:latest`.
  - `docker compose up -d` -> Containers created and started; both `lux-backend` and `lux-frontend` reported `Up (healthy)` status.
  - Container health endpoints:
    - `curl http://localhost:8000/health` -> `{"status":"ok","app":"lux"}` (HTTP 200).
    - `curl http://localhost:3000/health` -> `{"status":"ok","app":"lux"}` (HTTP 200, reverse-proxied via Nginx).
    - `curl http://localhost:3000/api/v1/health` -> `{"status":"ok","app":"lux"}` (HTTP 200, reverse-proxied via Nginx).
    - `curl http://localhost:3000/` -> Served SPA with `<title>Lux — Data Observability Platform</title>`.
  - End-to-end containerized scenario execution:
    - `POST http://localhost:3000/api/v1/scenarios/monday_revenue_mystery/load` -> Loaded 4 datasets, 8 rules, 16 DAG nodes.
    - `POST http://localhost:3000/api/v1/validations/run` -> Detected 4 failed checks and 4 passed checks in 137ms.
    - `POST http://localhost:3000/api/v1/recovery/verify` -> Restored quality health to `HEALTHY`, resolved all 4 defects, confirmed `ALL_ASSETS_HEALTHY`.
  - `docker compose down` -> Cleanly stopped and removed containers and network.
  - `cd backend && pytest` -> 254 passed across 22 test files in 16.32s (zero regressions).
  - `cd backend && ruff check .` -> All checks passed! (0 lint errors).
  - `cd backend && ruff format --check .` -> 92 files already formatted.
  - `cd backend && mypy app` -> Success: no issues found in 64 source files.
  - `cd frontend && npm test` -> 149 passed across 29 test files in 57.26s.
  - `cd frontend && npm run lint` -> `eslint .` exited with code 0 (0 warnings/errors).
  - `cd frontend && npm run typecheck` -> `tsc --noEmit` exited with code 0 (0 errors).
  - `cd frontend && npm run build` -> `tsc && vite build` built production bundle in 5.61s.
- **Remaining Limitations:** None. Task T24 and Milestone M8 are completely fulfilled. The full Lux Data Observability Platform is operational and verified.















