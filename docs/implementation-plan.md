# Lux Implementation Plan & Task Backlog

## 1. Quality Standards: Definition of Ready & Definition of Done

### Definition of Ready (DoR)
A task is **Ready** for implementation only when:
1. All prerequisite task IDs are completed and verified in [`docs/progress.md`](file:///d:/Projects/lux-data-observability/docs/progress.md).
2. The task scope, acceptance criteria, and edge cases are unambiguously specified.
3. Relevant architectural decisions (ADRs) have been accepted.
4. Input schemas and expected interfaces are documented in [`docs/api-contracts.md`](file:///d:/Projects/lux-data-observability/docs/api-contracts.md) and [`docs/data-model.md`](file:///d:/Projects/lux-data-observability/docs/data-model.md).
5. Any required human approvals have been granted.

### Shared Definition of Done (DoD)
A task is **Done** only when:
1. **Observable Acceptance:** All task-specific acceptance criteria are verified with automated tests or observable UI/API behavior.
2. **Automated Testing:** Unit and/or integration tests are written and passing with 0 failures (`pytest` for backend, `vitest` for frontend).
3. **Type Safety & Linting:** Code passes static analysis without errors (`mypy app`, `ruff check .`, `npm run typecheck`, `npm run lint`).
4. **Security Integrity:** Input validation, path sanitization, and XSS auto-escaping are strictly enforced where applicable.
5. **No Regressions:** All existing tests continue to pass.
6. **Documentation & Tracking:** [`docs/progress.md`](file:///d:/Projects/lux-data-observability/docs/progress.md) is updated with task status, verification evidence, and key implementation notes.

---

## 2. Milestone Overview

- **Milestone 0: Core Foundation, Tooling & Scaffolding** (`T01`, `T02`)
- **Milestone 1: Persistence, Scenario Data Foundation & Ingestion Engine** (`T03`, `T04`, `T05`)
- **Milestone 2: Deterministic Data Quality Validation Engine** (`T06`, `T07`, `T08`)
- **Milestone 3: Lineage Graph & Downstream Impact Analysis** (`T09`, `T10`, `T11`)
- **Milestone 4: Pipeline Observability & Run History** (`T12`, `T13`)
- **Milestone 5: Incident Investigation & Safe Report Generation** (`T14`, `T15`)
- **Milestone 6: Frontend "Trace the Failure" Interactive UI** (`T16`, `T17`, `T18`, `T19`, `T20`)
- **Milestone 7: Recovery Verification & End-to-End Acceptance** (`T21`, `T22`, `T23`)
- **Milestone 8: Containerization & Polish** (`T24`)

---

## 3. Detailed Implementation Backlog

### Task T01: Backend Scaffolding, Tooling & Base Configuration
- **Status:** COMPLETED
- **Objective:** Establish the Python backend application skeleton with FastAPI, Pydantic v2, Ruff linter, Mypy type checker, and Pytest test harness.
- **Prerequisites:** None.
- **In-Scope:**
  - Create `backend/pyproject.toml` with dependencies (`fastapi`, `uvicorn`, `pydantic>=2.0`, `pydantic-settings`, `sqlalchemy>=2.0`, `networkx`, `jinja2`, `python-multipart`).
  - Configure dev tools: `ruff`, `mypy`, `pytest`, `pytest-asyncio`.
  - Create `backend/app/main.py` with FastAPI initialization, health check endpoint (`GET /health`), CORS middleware, and global error handling envelope.
  - Setup `backend/app/core/config.py` using `pydantic-settings` to manage environment configuration safely.
  - Create base test file `backend/tests/test_health.py`.
- **Out-of-Scope:** Business logic, database schemas, frontend integration.
- **Acceptance Criteria:**
  - `GET /health` returns `{"status": "ok", "app": "lux"}` with HTTP 200.
  - `pytest` executes and passes.
  - `ruff check .` and `mypy app` run with zero errors.
- **Commands to Run:**
  - `cd backend && pip install -e ".[dev]"`
  - `cd backend && pytest`
  - `cd backend && ruff check . && mypy app`
- **Edge Cases & Risks:** Python 3.13 compatibility with dependencies; resolve with modern pinned versions.
- **Complexity:** Low.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T02: Frontend Scaffolding, Tooling & Lux Purple Theme Tokens
- **Objective:** Initialize the React 18+ TypeScript SPA using Vite, configure Tailwind CSS with the accessible Lux Purple color system, and setup Vitest.
- **Prerequisites:** None.
- **In-Scope:**
  - Initialize `frontend/package.json` with React, TypeScript, Vite, Tailwind CSS, Lucide React icons, and Vitest.
  - Configure `tailwind.config.js` and `src/styles/tokens.css` with the Lux Purple palette (`#6B46C1` primary, `#7C3AED` hover, high-contrast dark slates `#0F172A`, `#1E293B`, and accessible status tokens).
  - Setup `src/App.tsx` shell with Lux header, logo, and semantic navigation tabs.
  - Setup Vitest and React Testing Library in `frontend/tests/App.test.tsx`.
- **Out-of-Scope:** Complex graphs, API calls, or scenario views.
- **Acceptance Criteria:**
  - Frontend dev server boots and renders the Lux header with accessible purple tokens.
  - `npm test` executes and passes initial App shell test.
  - `npm run lint` and `npm run typecheck` run clean with zero errors.
- **Commands to Run:**
  - `cd frontend && npm install`
  - `cd frontend && npm test -- --run`
  - `cd frontend && npm run typecheck && npm run lint`
- **Edge Cases & Risks:** Ensure WCAG AA contrast for text on purple backgrounds (>=4.5:1).
- **Complexity:** Low.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T03: Relational Database Schema & SQLite Persistence Engine
- **Objective:** Implement the SQLite persistence layer with WAL mode and SQLAlchemy 2.0 ORM models matching [`docs/data-model.md`](file:///d:/Projects/lux-data-observability/docs/data-model.md).
- **Prerequisites:** `T01`.
- **In-Scope:**
  - Database connection session factory in `backend/app/db/session.py` with `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON`.
  - SQLAlchemy 2.0 ORM models in `backend/app/models/`: `Scenario`, `Dataset`, `ValidationRule`, `ValidationRun`, `ValidationFinding`, `LineageNode`, `LineageEdge`, `PipelineRun`, `FreshnessCheck`, `Investigation`, `ReportArtifact`.
  - Database table initialization utility `backend/app/db/init_db.py`.
  - Integration test asserting table creation and cascade delete behavior.
- **Out-of-Scope:** Data ingestion or rule execution.
- **Acceptance Criteria:**
  - Database initializes `data/lux.db` in WAL mode with all 11 tables and indices.
  - Automated integration test verifies entity relationships, cascades, and constraints.
- **Commands to Run:**
  - `cd backend && pytest tests/integration/test_db.py`
- **Edge Cases & Risks:** Concurrency file locks in SQLite; ensure WAL mode and busy timeout are configured.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T04: Bundled Signature Fixtures & Scenario Metadata Definition
- **Objective:** Create the deterministic synthetic e-commerce fixtures and metadata for the signature scenario *Monday Revenue Mystery*.
- **Prerequisites:** None.
- **In-Scope:**
  - Create directory `data/scenarios/monday_revenue_mystery/`.
  - Create `scenario.json`: metadata, 4 dataset schemas (`orders`, `order_items`, `products`, `inventory`), and complete 16-node lineage DAG with edges.
  - Create `rules.json`: declarative quality rules matching the defect catalog.
  - Create `pipeline_history.json`: historical run logs and SLA specs.
  - Create defective fixtures in `defective/`:
    - `orders.csv` (1,250 rows, 15 duplicate order IDs).
    - `order_items.csv` (3,420 rows, 24 broken foreign keys).
    - `products.csv` (250 rows).
    - `inventory.csv` (250 rows, 8 negative quantities).
  - Create clean fixtures in `corrected/` with all defects resolved.
  - Unit test verifying fixture row counts and synthetic defect presence.
- **Out-of-Scope:** Database loading or API routers.
- **Acceptance Criteria:**
  - Exact counts match: 1,250 orders, 3,420 order items, 250 products, 250 inventory records.
  - Defective fixtures contain exactly 15 duplicate order IDs, 24 orphaned items, 8 negative inventory rows.
  - Corrected fixtures contain 0 duplicates, 0 orphaned items, 0 negative inventory rows.
- **Commands to Run:**
  - `cd backend && pytest tests/unit/test_fixtures.py`
- **Edge Cases & Risks:** Ensure CSV line endings (LF) and UTF-8 encoding without BOM.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T05: Dataset Ingestion, Scenario Loader & Upload Security Service
- **Objective:** Build the ingestion service to load bundled scenarios and handle safe file uploads.
- **Prerequisites:** `T01`, `T03`, `T04`.
- **In-Scope:**
  - Ingestion service in `backend/app/services/ingestion/`: scenario loader, CSV/JSON chunked streaming reader, dataset metadata extractor.
  - Secure upload handler enforcing 20MB max size, extension whitelist (`.csv`, `.json`), UUID directory isolation, and canonical path traversal verification.
  - REST endpoints: `GET /api/v1/scenarios`, `POST /api/v1/scenarios/{id}/load`, `GET /api/v1/datasets`, `GET /api/v1/datasets/{id}/preview`, `POST /api/v1/datasets/upload`.
  - Integration tests verifying scenario loading, preview pagination, and upload security protections.
- **Out-of-Scope:** Validation rule evaluation or lineage traversal.
- **Acceptance Criteria:**
  - `POST /api/v1/scenarios/monday_revenue_mystery/load` populates SQLite and returns HTTP 200.
  - `GET /api/v1/datasets/orders/preview?limit=10` returns exact preview rows.
  - File uploads >20MB return HTTP 413; path traversal payloads return HTTP 400.
- **Commands to Run:**
  - `cd backend && pytest tests/integration/test_ingestion_api.py`
- **Edge Cases & Risks:** Malformed delimiters, path traversal in multipart filenames.
- **Complexity:** Medium.
- **Context-Budget Risk:** Medium.
- **Approvals Required:** None.

---

### Task T06: Validation Rule Framework & Core Rule Evaluators
- **Objective:** Implement the extensible validation engine and core rule evaluators for null checks, uniqueness, type validity, record counts, and value ranges.
- **Prerequisites:** `T01`, `T03`.
- **In-Scope:**
  - Base rule protocol `BaseValidationRule` in `backend/app/services/validation/base.py`.
  - Core rule evaluators:
    - `NullCheckRule`: Detects nulls/blanks in required fields.
    - `UniquenessRule`: Detects duplicate primary keys and composite keys.
    - `TypeValidityRule`: Validates integer/float parseability and regex formats.
    - `RecordCountRule`: Checks row count thresholds.
    - `ValueRangeRule`: Asserts min/max numeric bounds (e.g., quantity >= 0).
  - Rule registry for dynamic instantiation from declarative parameters.
  - Unit tests for all core rule evaluators with sample clean and dirty records.
- **Out-of-Scope:** Multi-dataset cross-referencing or temporal checks.
- **Acceptance Criteria:**
  - `UniquenessRule` accurately detects 15 duplicates in `orders.csv` sample with line indices and keys.
  - `ValueRangeRule` accurately detects 8 negative inventory SKUs in `inventory.csv`.
  - Unit test suite passes with >90% code coverage.
- **Commands to Run:**
  - `cd backend && pytest tests/unit/test_rules_core.py`
- **Edge Cases & Risks:** String whitespace-only cells treated as nulls; ensure strict stripping.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T07: Relational, Temporal & Schema Rule Evaluators
- **Objective:** Implement advanced rule evaluators for referential integrity, timestamp temporal anomalies, schema consistency, and freshness.
- **Prerequisites:** `T06`.
- **In-Scope:**
  - `ReferentialIntegrityRule`: Cross-references foreign keys across datasets (e.g., `order_items.product_id` in `products.product_id`).
  - `TemporalAnomalyRule`: Parses ISO timestamps, detects future timestamps, and detects temporal gaps exceeding threshold.
  - `SchemaIntegrityRule`: Validates column existence, missing expected columns, and type drift.
  - `FreshnessRule`: Evaluates partition date recency vs expected SLA hours.
  - Unit tests for referential integrity and temporal rules.
- **Out-of-Scope:** API persistence or runner orchestration.
- **Acceptance Criteria:**
  - `ReferentialIntegrityRule` detects 24 orphaned items in `order_items.csv` missing from `products.csv`.
  - `TemporalAnomalyRule` detects Sunday evening transaction gap in `orders.csv`.
  - Unit tests pass with 100% assertions satisfied.
- **Commands to Run:**
  - `cd backend && pytest tests/unit/test_rules_relational.py`
- **Edge Cases & Risks:** Large foreign key lookup sets; use in-memory Python sets for O(1) membership checks.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T08: Validation Runner Service, Persistence & Structured Findings API
- **Objective:** Create the validation runner service that executes rules against datasets, persists runs and granular findings to SQLite, and exposes REST endpoints.
- **Prerequisites:** `T03`, `T05`, `T06`, `T07`.
- **In-Scope:**
  - `ValidationRunnerService` in `backend/app/services/validation/runner.py`.
  - Structured evidence generation: rule ID, category, severity, status, affected count, sample rows, duration ms.
  - Persistence of `ValidationRun` and `ValidationFinding` records.
  - REST endpoints:
    - `POST /api/v1/validations/run`: Execute validation run.
    - `GET /api/v1/validations/runs/{id}`: Run summary.
    - `GET /api/v1/validations/runs/{id}/findings`: Filterable findings.
  - Integration tests for validation execution against *Monday Revenue Mystery*.
- **Out-of-Scope:** Downstream impact traversal or frontend views.
- **Acceptance Criteria:**
  - Executing validation run against defective fixtures produces exactly 4 failed checks and expected finding counts.
  - Findings contain structured sample duplicate keys and broken foreign key IDs.
  - Integration tests pass.
- **Commands to Run:**
  - `cd backend && pytest tests/integration/test_validations_api.py`
- **Edge Cases & Risks:** Large error sets; sample evidence rows must be capped at 50 sample items to prevent unbounded JSON payloads.
- **Complexity:** Medium.
- **Context-Budget Risk:** Medium.
- **Approvals Required:** None.

---

### Task T09: Lineage DAG Domain Engine & Graph Integrity Validator
- **Objective:** Build the in-memory NetworkX-backed Lineage Graph engine to represent pipeline dependencies and enforce DAG integrity.
- **Prerequisites:** `T01`, `T03`.
- **In-Scope:**
  - `LineageGraph` domain class in `backend/app/services/lineage/graph.py` encapsulating `networkx.DiGraph`.
  - Graph integrity validator: checks for cycles (`nx.is_directed_acyclic_graph`), dangling references, isolated nodes.
  - Traversal methods: `get_upstream_nodes(node_id)`, `get_downstream_nodes(node_id)`, `topological_sort()`.
  - Seed loader to construct graph from `scenario.json` metadata.
  - Unit tests asserting DAG cycle rejection and correct ancestor/descendant traversal.
- **Out-of-Scope:** Impact classification logic or UI rendering.
- **Acceptance Criteria:**
  - Cyclic graphs are rejected with `CyclicDependencyError` detailing the cycle path.
  - Valid scenario graph of 16 nodes and 14 edges loads cleanly.
  - Unit tests verify upstream ancestors of `report_exec_dash` include `orders` and `order_items`.
- **Commands to Run:**
  - `cd backend && pytest tests/unit/test_lineage_graph.py`
- **Edge Cases & Risks:** Disconnected components in graph; ensure isolated nodes are handled gracefully.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T10: Downstream Impact Analysis Engine & Blast Radius Classifier
- **Objective:** Implement the impact analysis service to trace downstream paths from any failed check, dataset, or node and categorize impact levels.
- **Prerequisites:** `T08`, `T09`.
- **In-Scope:**
  - `ImpactAnalysisService` in `backend/app/services/impact/analyzer.py`.
  - Impact classification logic:
    - `CONFIRMED_FAILED`: Directly failed a validation.
    - `DIRECTLY_AFFECTED`: Immediate child of corrupted node.
    - `POTENTIALLY_AFFECTED`: Transitive downstream descendant.
    - `HEALTHY`: Passing checks or no upstream failures.
  - Path explanation builder constructing step-by-step dependency breadcrumbs.
  - Unit tests verifying impact blast radius calculation for `orders.csv` and finding `VAL-ORD-001`.
- **Out-of-Scope:** REST API endpoints or UI views.
- **Acceptance Criteria:**
  - Tracing `orders.csv` identifies `dim_orders` as `DIRECTLY_AFFECTED`, and `agg_daily_revenue`, `metric_revenue`, `report_exec_dash` as `POTENTIALLY_AFFECTED`.
  - Explanations list complete path from source to target.
- **Commands to Run:**
  - `cd backend && pytest tests/unit/test_impact_analysis.py`
- **Edge Cases & Risks:** Multiple paths to same downstream node; compute shortest path and deduplicate impact items.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T11: Lineage & Impact REST API Endpoints
- **Objective:** Expose REST endpoints for lineage graph exploration, node details, and impact tracing.
- **Prerequisites:** `T09`, `T10`.
- **In-Scope:**
  - REST endpoints:
    - `GET /api/v1/lineage`: Returns nodes and edges formatted for React Flow, with Dagre-calculated `(x, y)` coordinates.
    - `GET /api/v1/lineage/nodes/{id}`: Detailed node metadata and direct upstream/downstream connections.
    - `POST /api/v1/lineage/validate`: Validates declared lineage definitions.
    - `POST /api/v1/impact/trace`: Calculates impact blast radius from target ID.
  - Integration tests verifying contract schemas and React Flow payload structure.
- **Out-of-Scope:** Frontend rendering.
- **Acceptance Criteria:**
  - `GET /api/v1/lineage` returns 16 nodes with valid numeric `position.x` and `position.y`.
  - `POST /api/v1/impact/trace` returns affected asset list matching API contract.
  - Integration tests pass.
- **Commands to Run:**
  - `cd backend && pytest tests/integration/test_lineage_api.py`
- **Edge Cases & Risks:** Graph layout collisions; Dagre spacing parameters tuned for readability.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T12: Pipeline Run History & Execution vs Quality Dual-Dimension Tracker
- **Objective:** Implement the pipeline run persistence service and API, enforcing the dual-dimension status model (Compute Execution Status vs Data Quality Health).
- **Prerequisites:** `T03`, `T08`.
- **In-Scope:**
  - Pipeline history service in `backend/app/services/pipeline/service.py`.
  - Dual-dimension status evaluation logic per [`docs/decisions/ADR-006-separation-of-pipeline-health-and-data-quality.md`](file:///d:/Projects/lux-data-observability/docs/decisions/ADR-006-separation-of-pipeline-health-and-data-quality.md).
  - Seed historical pipeline run records from `pipeline_history.json`.
  - REST endpoints: `GET /api/v1/pipelines/runs`, `GET /api/v1/pipelines/runs/{id}`.
  - Integration test asserting that the overnight run returns `COMPLETED_SUCCESS` for execution while returning `CORRUPTED` for quality health.
- **Out-of-Scope:** Real-time cron scheduler or external orchestrator integration.
- **Acceptance Criteria:**
  - API returns historical runs with duration, record counts, and step logs.
  - Accurately demonstrates "Pipeline execution succeeded, but data is corrupted."
- **Commands to Run:**
  - `cd backend && pytest tests/integration/test_pipeline_api.py`
- **Edge Cases & Risks:** Missing step logs; default to empty list.
- **Complexity:** Low.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T13: Dataset Partition Freshness & SLA Monitoring Service
- **Objective:** Implement dataset freshness evaluation comparing observed partition timestamps against declared SLA thresholds.
- **Prerequisites:** `T05`, `T12`.
- **In-Scope:**
  - Freshness monitoring logic in `backend/app/services/pipeline/freshness.py`.
  - Comparison of expected partition timestamp vs max observed timestamp in dataset.
  - Status classification: `FRESH`, `STALE`, `MISSING`.
  - REST endpoint: `GET /api/v1/pipelines/freshness`.
  - Integration test verifying freshness detection for *Monday Revenue Mystery*.
- **Out-of-Scope:** Live streaming timestamp listeners.
- **Acceptance Criteria:**
  - `GET /api/v1/pipelines/freshness` identifies `orders.csv` as `STALE` (5.99 hours behind SLA).
  - Integration test passes.
- **Commands to Run:**
  - `cd backend && pytest tests/integration/test_freshness_api.py`
- **Edge Cases & Risks:** Missing or invalid timestamps; handled safely with `MISSING` status.
- **Complexity:** Low.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T14: Investigation Workspace Engine & Schema Integration
- **Objective:** Implement the investigation service to manage structured investigation states, separating verified facts, working hypotheses, and action items.
- **Prerequisites:** `T03`, `T08`, `T10`.
- **In-Scope:**
  - Investigation service in `backend/app/services/reports/investigation.py`.
  - REST endpoints: `POST /api/v1/investigations`, `GET /api/v1/investigations/{id}`.
  - Integration tests verifying investigation lifecycle and item persistence.
- **Out-of-Scope:** HTML report rendering.
- **Acceptance Criteria:**
  - Investigation workspace saves verified facts, hypotheses, and action items.
  - Facts cannot be confused with hypotheses in the schema.
- **Commands to Run:**
  - `cd backend && pytest tests/integration/test_investigations_api.py`
- **Edge Cases & Risks:** Empty action items list; handled cleanly.
- **Complexity:** Low.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T15: Safe Report Generator Service (JSON & HTML with Jinja2 Autoescape & CSP)
- **Objective:** Implement the report generator producing immutable JSON and safe, styled HTML reports with strict Jinja2 auto-escaping and CSP headers.
- **Prerequisites:** `T14`.
- **In-Scope:**
  - Report generator in `backend/app/services/reports/generator.py`.
  - Jinja2 HTML report template with Lux Purple branding, inlined CSS, and collapsible `<details>` evidence panels.
  - Security enforcement: auto-escape enabled, CSP `<meta>` header, SHA-256 hash calculation, storage in `data/artifacts/`.
  - REST endpoints: `POST /api/v1/reports/generate`, `GET /api/v1/reports/{id}/export?format=json|html`.
  - Unit and security tests asserting that XSS payloads in CSV values are rendered as safe HTML entities and CSP header is present.
- **Out-of-Scope:** External PDF rendering engines.
- **Acceptance Criteria:**
  - Exported HTML report renders cleanly in browser with zero external dependencies.
  - Security tests verify that `<script>alert(1)</script>` in dataset cells is escaped to `&lt;script&gt;`.
  - Exported JSON satisfies the report JSON schema.
- **Commands to Run:**
  - `cd backend && pytest tests/unit/test_report_sanitization.py`
  - `cd backend && pytest tests/integration/test_reports_api.py`
- **Edge Cases & Risks:** Unicode characters in CSV values; UTF-8 encoding strictly enforced.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T16: Frontend Navigation Shell, Scenario Switcher & Dataset Inspector
- **Objective:** Build the core frontend application layout, scenario selector, dataset summary view, and file upload modal.
- **Prerequisites:** `T02`, `T05`.
- **In-Scope:**
  - Typed API client in `frontend/src/api/` using Fetch API with error handling.
  - `AppHeader`: Lux Purple branding, scenario selector dropdown, status indicator.
  - `ScenarioManager`: Scenario loader button, dataset preview modal with pagination.
  - `UploadModal`: Drag-and-drop file upload with format and size validation.
  - Vitest component tests.
- **Out-of-Scope:** Interactive lineage DAG or report generation views.
- **Acceptance Criteria:**
  - User can select "Monday Revenue Mystery" and trigger scenario loading.
  - Datasets list displays row counts and columns.
  - Component tests pass.
- **Commands to Run:**
  - `cd frontend && npm test -- --run`
- **Edge Cases & Risks:** Network failure handling with accessible error toast/alert banner.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T17: Quality Validation Findings Explorer & Evidence Drawer UI
- **Objective:** Build the validation findings dashboard with summary cards, severity/status filters, findings table, and slide-over row evidence drawer.
- **Prerequisites:** `T08`, `T16`.
- **In-Scope:**
  - `ValidationSummaryCards`: Total checks, passed, failed, warnings, execution duration.
  - `FindingsTable`: Filterable by severity (`CRITICAL`, `HIGH`, etc.), status, and dataset.
  - `EvidenceDrawer`: Slide-over drawer displaying sample duplicate rows, broken foreign keys, and line numbers.
  - "Trace Impact" action button on findings rows.
  - Vitest component tests.
- **Out-of-Scope:** DAG canvas visualization.
- **Acceptance Criteria:**
  - Clicking a finding opens the evidence drawer displaying sample rows and observed vs expected values.
  - Filtering by `CRITICAL` isolates duplicate order checks.
  - Component tests pass.
- **Commands to Run:**
  - `cd frontend && npm test -- --run`
- **Edge Cases & Risks:** Accessible keyboard focus trap in slide-over drawer.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T18: Interactive Lineage DAG & Blast Radius Visualization UI
- **Objective:** Implement the interactive Lineage DAG visualizer using React Flow, rendering node hierarchies, dual-dimension status badges, and impact path highlighting.
- **Prerequisites:** `T11`, `T16`.
- **In-Scope:**
  - React Flow (`@xyflow/react`) integration in `frontend/src/components/lineage/`.
  - Custom node components for `SOURCE_DATASET`, `TRANSFORMATION`, `DERIVED_DATASET`, `METRIC`, and `REPORT`.
  - Dual-dimension status chips on nodes: Compute Status (terminal icon) and Quality Health (badge).
  - Interactive path highlighting: clicking a node or finding highlights upstream ancestors and downstream impact paths with distinct styling.
  - Zoom, pan, and minimap controls.
  - Vitest component tests.
- **Out-of-Scope:** Node editing or authoring new DAG pipelines.
- **Acceptance Criteria:**
  - Lineage DAG renders all 16 nodes with clear visual hierarchy.
  - Selecting `src_orders` highlights downstream path through to `report_exec_dash`.
  - Component tests pass.
- **Commands to Run:**
  - `cd frontend && npm test -- --run`
- **Edge Cases & Risks:** High DPI screen canvas scaling; React Flow handles natively.
- **Complexity:** High.
- **Context-Budget Risk:** Medium.
- **Approvals Required:** None.

---

### Task T19: Pipeline Observability, Freshness & Run History UI
- **Objective:** Build the pipeline execution history timeline and partition freshness monitoring views.
- **Prerequisites:** `T12`, `T13`, `T16`.
- **In-Scope:**
  - `PipelineHistoryView`: Execution run timeline, duration bar charts, and step logs.
  - Visual callout highlighting: "Execution Succeeded (Exit 0) but Data Quality is Corrupted".
  - `FreshnessView`: Visual status cards for dataset partitions with SLA hours and freshness status badges.
  - Vitest component tests.
- **Out-of-Scope:** External CI/CD dashboard integrations.
- **Acceptance Criteria:**
  - Clearly renders the overnight pipeline run with `SUCCESS` compute badge alongside `CORRUPTED` data health badge.
  - Freshness panel displays `orders.csv` partition staleness.
- **Commands to Run:**
  - `cd frontend && npm test -- --run`
- **Edge Cases & Risks:** Responsive layout on smaller screen resolutions.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T20: Investigation Workspace & Report Export Modal UI
- **Objective:** Build the investigation view and report generation modal with live JSON and HTML preview and download actions.
- **Prerequisites:** `T15`, `T17`, `T18`.
- **In-Scope:**
  - `InvestigationWorkspace`: Displays confirmed observations, working hypotheses, and remediation checklist.
  - `ReportModal`: "Generate Report" action triggering report creation.
  - In-app tabbed preview of sanitized HTML and formatted JSON report.
  - Direct download links for `.html` and `.json` artifacts.
  - Vitest component tests.
- **Out-of-Scope:** Multi-user collaborative commenting.
- **Acceptance Criteria:**
  - User can generate an incident report and download both HTML and JSON formats.
  - Downloaded HTML file opens locally in a browser with full styles and zero errors.
- **Commands to Run:**
  - `cd frontend && npm test -- --run`
- **Edge Cases & Risks:** Blob URL cleanup after file downloads to prevent memory leaks.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T21: Recovery Verification Backend Engine
- **Objective:** Implement the backend recovery verification service that swaps to clean fixtures, re-executes validations, compares historical runs, and evaluates downstream recovery.
- **Prerequisites:** `T08`, `T10`, `T12`.
- **In-Scope:**
  - `RecoveryService` in `backend/app/services/validation/recovery.py`.
  - Re-execution of rules against `corrected/` dataset files.
  - Before-and-after diff calculation: comparing previous run findings to current run findings.
  - Verification that downstream assets transition from `AFFECTED` to `HEALTHY`.
  - REST endpoint: `POST /api/v1/recovery/verify`.
  - Integration test asserting recovery of *Monday Revenue Mystery*.
- **Out-of-Scope:** Automatic destructive overwriting of original dirty files.
- **Acceptance Criteria:**
  - Re-executing against corrected fixtures yields 0 failed checks.
  - Comparison diff lists all 4 previously failed checks as `RESOLVED`.
  - Quality health transitions to `HEALTHY`.
- **Commands to Run:**
  - `cd backend && pytest tests/integration/test_recovery_api.py`
- **Edge Cases & Risks:** Partial fixes (e.g. 1 check still failing); must report partial recovery accurately.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T22: Recovery Verification Frontend View
- **Objective:** Build the recovery verification UI view displaying side-by-side comparison tables, resolution status indicators, and downstream recovery badges.
- **Prerequisites:** `T20`, `T21`.
- **In-Scope:**
  - `RecoveryDiffView`: Side-by-side table comparing Before (Defective) vs After (Corrected) runs.
  - Resolved checks checklist with green checkmarks and duration comparison.
  - Downstream asset recovery banner confirming restored trust in reports.
  - Vitest component tests.
- **Out-of-Scope:** Automated production data hot-patching.
- **Acceptance Criteria:**
  - User can click "Verify Recovery", view the before-and-after diff, and observe that all findings are resolved.
- **Commands to Run:**
  - `cd frontend && npm test -- --run`
- **Edge Cases & Risks:** Highlighting remaining warnings if a check is only partially resolved.
- **Complexity:** Low.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T23: Signature Scenario End-to-End Test Suite
- **Objective:** Implement a comprehensive automated end-to-end acceptance test covering the entire 8-step "Trace the Failure" workflow for *Monday Revenue Mystery*.
- **Prerequisites:** `T01` through `T22`.
- **In-Scope:**
  - Scenario acceptance test `backend/tests/scenarios/test_monday_revenue_mystery.py`.
  - Programmatic verification of the complete workflow:
    1. Load scenario.
    2. Execute validations (verify 4 failures).
    3. Assert structured row evidence.
    4. Assert lineage DAG traversal.
    5. Assert downstream impact blast radius.
    6. Assert pipeline execution `SUCCESS` vs quality `CORRUPTED`.
    7. Generate and sanitize HTML/JSON reports.
    8. Verify recovery with clean fixture (all passing).
- **Out-of-Scope:** Third-party cloud deployment tests.
- **Acceptance Criteria:**
  - Test executes seamlessly in CI/local environment in < 2 seconds.
  - 100% assertions pass across all 8 workflow stages.
- **Commands to Run:**
  - `cd backend && pytest tests/scenarios/test_monday_revenue_mystery.py`
- **Edge Cases & Risks:** Flaky timing; all steps are strictly deterministic and run in-memory/SQLite.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

---

### Task T24: Docker Compose Orchestration, Production Build & Operational Documentation
- **Status:** COMPLETED
- **Objective:** Finalize containerization with Docker Compose, verify production builds, and update operational documentation.
- **Prerequisites:** `T23`.
- **In-Scope:**
  - Multi-stage `backend/Dockerfile` and `frontend/Dockerfile`.
  - `docker-compose.yml` orchestrating backend and frontend with persistent `data/` volume mount.
  - Verify container builds and startup.
  - Update `README.md` with complete architecture overview, verified quickstart instructions, and screenshots/diagrams.
- **Out-of-Scope:** Paid cloud deployment scripts (AWS/GCP).
- **Acceptance Criteria:**
  - `docker compose build` succeeds with zero errors.
  - Complete application functions locally in Docker stack without external dependencies.
- **Commands to Run:**
  - `docker compose build`
- **Edge Cases & Risks:** Windows/Linux path separator differences in volume mounts; use forward slashes.
- **Complexity:** Medium.
- **Context-Budget Risk:** Low.
- **Approvals Required:** None.

