# Lux Testing Strategy & Quality Assurance

## 1. Testing Pyramid & Quality Gates

Lux enforces strict automated testing across all layers of the platform to ensure data integrity, security, and algorithmic reliability.

```text
               ▲
              / \
             /   \     E2E Scenario Tests (Monday Revenue Mystery)
            /  5% \    - End-to-End "Trace the Failure" verification
           /───────\
          /         \   Integration Tests (API & DB)
         /   25%     \  - FastAPI endpoints, SQLite WAL persistence, uploads
        /─────────────\
       /               \ Unit Tests (Services & Rules)
      /      70%        \ - Validation rules, NetworkX DAG, Jinja2 autoescape
     /───────────────────\
```

### Coverage Objectives
- **Unit Test Coverage:** > 90% for validation rules, graph traversal algorithms, and report generation sanitizers.
- **Integration Test Coverage:** 100% of REST API endpoints tested with happy path, validation error, and edge cases.
- **Scenario Verification:** 100% deterministic assertion of findings in the signature scenario *Monday Revenue Mystery*.

---

## 2. Testing Layers

### 2.1 Backend Unit Testing (`backend/tests/unit`)
- **Validation Engine Rules (`test_rules_*.py`):**
  - Null/Required value detection across dirty and clean columns.
  - Primary key uniqueness on single and composite keys.
  - Foreign key referential integrity with orphaned child records.
  - Value range boundaries (negative values, extreme outliers).
  - Date and timestamp parsing with temporal gap detection.
- **Lineage Graph Traversal (`test_lineage_graph.py`):**
  - Directed Acyclic Graph validation (acyclicity verification).
  - Cycle rejection (raising structured `CyclicDependencyError`).
  - Correct identification of upstream ancestors and downstream descendants.
  - Dagre layout position assignment.
- **Impact Analysis Calculation (`test_impact_analysis.py`):**
  - Accurate classification of `CONFIRMED_FAILED`, `DIRECTLY_AFFECTED`, `POTENTIALLY_AFFECTED`.
  - Generation of deterministic dependency paths.
- **Report Security & Sanitization (`test_report_sanitization.py`):**
  - Verification that XSS payloads (`<script>`, `onload=`) inside CSV values are converted to safe HTML entities in HTML reports.
  - Content Security Policy (CSP) `<meta>` tag presence in exported HTML.
  - Valid JSON schema compliance in JSON exports.

### 2.2 Backend Integration Testing (`backend/tests/integration`)
- **API Router Verification (`test_api_*.py`):**
  - Test all endpoints in `backend/app/api/v1/`.
  - HTTP 200/201 status codes, error status codes (400, 404, 413, 422).
  - Database transactional rollback on failure.
- **Ingestion & Uploads (`test_ingestion_api.py`):**
  - CSV and JSON upload parsing.
  - File size limit rejection (>20MB returns 413).
  - Path traversal rejection (`../../etc/passwd` filenames).

### 2.3 Signature Scenario Acceptance Tests (`backend/tests/scenarios`)
- **Monday Revenue Mystery Suite (`test_monday_revenue_mystery.py`):**
  - Loads `monday_revenue_mystery` defective fixtures.
  - Asserts that all 4 expected defects are detected with exact record counts:
    - 15 duplicate order IDs (`VAL-ORD-001`).
    - 24 broken foreign keys (`VAL-ORD-002`).
    - 8 negative inventory quantities (`VAL-INV-001`).
    - 1 temporal gap / freshness warning (`VAL-FRESH-001`).
  - Asserts that downstream impact identifies `dim_orders`, `agg_daily_revenue`, `Metric: Total Daily Revenue`, and `Report: Executive Monday Dashboard`.
  - Loads corrected fixtures and verifies recovery: all checks pass (`PASSED`), and quality health shifts from `CORRUPTED` to `HEALTHY`.

### 2.4 Frontend Unit & Component Testing (`frontend/tests`)
- **Component Tests (Vitest + React Testing Library):**
  - `FindingsTable`: Rendering, filtering by severity and status, sorting, row selection.
  - `EvidenceDrawer`: Accurate formatting of sample records and diff values.
  - `LineageGraph`: Node status badge rendering (dual compute vs quality badges).
  - `RecoveryDiffView`: Before-and-after table comparisons.
- **Accessibility Testing:**
  - Automated WCAG AA contrast and semantic checks using `axe-core`.
  - Keyboard navigation through tables and modal dialogs.

---

## 3. Test Execution Commands

Once packages are installed during Milestone 0:

```bash
# Backend unit & integration tests
cd backend && pytest -v

# Scenario-specific acceptance tests
cd backend && pytest -v tests/scenarios/test_monday_revenue_mystery.py

# Type checking & linting
cd backend && mypy app && ruff check .

# Frontend component & unit tests
cd frontend && npm test -- --run

# Frontend type check & lint
cd frontend && npm run typecheck && npm run lint
```

