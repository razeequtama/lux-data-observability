# AGENTS.md — Coding Agent Operating Guidelines

Welcome to **Lux** (`lux-data-observability`).
This repository is an implementation of a data observability platform built for data engineers, software engineers, and analysts to validate data quality, trace dependency lineage, analyze downstream impact, monitor pipeline history, and investigate incidents.

---

## 1. Core Operating Principles

1. **Plan First, Then Implement:**
   - Always read [`docs/progress.md`](file:///d:/Projects/lux-data-observability/docs/progress.md) and [`docs/implementation-plan.md`](file:///d:/Projects/lux-data-observability/docs/implementation-plan.md) before picking up a task.
   - Work strictly on one backlog task at a time (e.g., `T01`, `T02`).
   - Do not jump ahead or implement features out of dependency order.
2. **Preserve Architectural Boundaries:**
   - Lux is structured as a **modular monolith**.
   - Do not create circular imports or bypass the service layer.
   - Separation of concerns: Ingestion → Validation Engine → Lineage & Graph → Impact Analysis → Pipeline History → Investigation/Reports → API → UI.
   - Distinct statuses: Differentiate pipeline execution health (`SUCCESS`, `FAILED`) from data quality health (`HEALTHY`, `DEGRADED`, `CORRUPTED`). A pipeline can execute with return code 0 while producing invalid data.
3. **No Decorative or Mocked Logic:**
   - Do not hardcode validation outputs, lineage edges, or incident conclusions.
   - Validation checks must execute genuine logic against dataset files.
   - Lineage must traverse declared dependency metadata.
   - Reports must reflect executed runs and observed findings.
   - Never introduce unsupported AI-based diagnoses or speculate beyond the evidence.
4. **Inspect Before Changing:**
   - Read relevant source code, schemas, and test fixtures before editing.
   - Never overwrite existing files wholesale when a targeted, surgical edit is sufficient.
   - Preserve existing docstrings, type annotations, and comments.

---

## 2. Directory Layout & Key Locations

```text
lux-data-observability/
├── AGENTS.md                          # This file: Agent guidelines & commands
├── README.md                          # Repository introduction & quickstart
├── docker-compose.yml                 # Local containerized orchestration
├── backend/                           # Python 3.13 / FastAPI application
│   ├── pyproject.toml                 # Backend dependencies & tool configs
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint
│   │   ├── api/                       # API routers (v1)
│   │   ├── core/                      # Config, logging, security, constants
│   │   ├── db/                        # SQLite connection, session, migrations
│   │   ├── models/                    # SQLAlchemy persistence models
│   │   ├── schemas/                   # Pydantic v2 domain & API schemas
│   │   ├── services/                  # Business logic engines
│   │   │   ├── ingestion/             # CSV/JSON loaders, scenario manager
│   │   │   ├── validation/            # Quality rules & validation runner
│   │   │   ├── lineage/               # DAG builder, validator & traversal
│   │   │   ├── impact/                # Downstream impact path tracer
│   │   │   ├── pipeline/              # Pipeline runs & freshness monitors
│   │   │   └── reports/               # Incident report generator (JSON & HTML)
│   │   └── storage/                   # Local file & artifact management
│   └── tests/                         # Pytest test suite
│       ├── unit/                      # Fast isolated unit tests
│       ├── integration/               # API & DB integration tests
│       └── scenarios/                 # Signature scenario verification tests
├── frontend/                          # React 18+ / TypeScript / Vite application
│   ├── package.json                   # Frontend dependencies
│   ├── vite.config.ts                 # Vite bundler config
│   ├── tsconfig.json                  # TypeScript compiler config
│   ├── src/
│   │   ├── main.tsx                   # React root entry
│   │   ├── App.tsx                    # Main app shell & routing
│   │   ├── api/                       # Typed API clients & fetchers
│   │   ├── components/                # Reusable UI components & layouts
│   │   │   ├── common/                # Buttons, tables, modals, badges, cards
│   │   │   ├── lineage/               # Interactive DAG visualizer (React Flow)
│   │   │   ├── validation/            # Findings tables, evidence inspectors
│   │   │   ├── impact/                # Downstream impact path viewer
│   │   │   └── reports/               # Investigation & report previewers
│   │   ├── hooks/                     # Custom React hooks
│   │   ├── types/                     # TypeScript domain models matching schemas
│   │   └── styles/                    # Design tokens (Lux Purple brand palette)
│   └── tests/                         # Vitest & React Testing Library tests
├── data/                              # Bundled scenarios & runtime storage
│   ├── scenarios/                     # Deterministic bundled scenarios
│   │   └── monday_revenue_mystery/    # Signature scenario fixtures & metadata
│   │       ├── scenario.json          # Scenario definition & lineage metadata
│   │       ├── rules.json             # Quality rule configurations
│   │       ├── pipeline_history.json  # Historical run records
│   │       ├── defective/             # Input files with introduced defects
│   │       └── corrected/             # Clean files for recovery verification
│   └── uploads/                       # Ephemeral runtime upload directory (.gitignored)
└── docs/                              # System documentation & specifications
    ├── product-requirements.md        # Full product specification (FR-01 to FR-09)
    ├── architecture.md                # System architecture & component design
    ├── implementation-plan.md         # Tasks T01-T24, dependencies, DoD
    ├── api-contracts.md               # Complete REST API specifications
    ├── data-model.md                  # Entity models, SQLite DDL, JSON schemas
    ├── security.md                    # Threat model, input sanitization, boundaries
    ├── testing-strategy.md            # Test pyramids, acceptance suites, fixtures
    ├── progress.md                    # Live implementation tracking
    └── decisions/                     # Architecture Decision Records (ADRs)
```

---

## 3. Verified Host Environment & Tooling

The host system has been inspected and verified with:
- **Python:** `3.13.5`
- **Node.js:** `v22.17.1`
- **Docker:** `29.8.2`
- **Operating System:** Windows (PowerShell environment)

---

## 4. Standard Commands & Verification

*(Note: Dependencies will be installed in tasks T01/T02. Once installed, use the following standardized commands).*

### Backend (Python / FastAPI)
- **Install dependencies (uv/pip):** `cd backend && pip install -e ".[dev]"`
- **Run linter (Ruff):** `cd backend && ruff check .`
- **Run formatter check:** `cd backend && ruff format --check .`
- **Run type checker (Mypy):** `cd backend && mypy app`
- **Run unit & integration tests:** `cd backend && pytest`
- **Run scenario verification:** `cd backend && pytest tests/scenarios/test_monday_revenue_mystery.py`
- **Run dev server:** `cd backend && uvicorn app.main:app --reload --port 8000`

### Frontend (React / TypeScript / Vite)
- **Install dependencies:** `cd frontend && npm install`
- **Run linter (ESLint):** `cd frontend && npm run lint`
- **Run type checker:** `cd frontend && npm run typecheck`
- **Run tests (Vitest):** `cd frontend && npm test`
- **Run dev server:** `cd frontend && npm run dev`
- **Build production assets:** `cd frontend && npm run build`

### Docker Compose
- **Build & start local stack:** `docker compose up --build`
- **Tear down stack:** `docker compose down -v`

---

## 5. Security & Safety Rules

- **Untrusted File Input:** All uploaded CSV and JSON files must be validated for size (max 20MB by default), MIME type, and schema before processing.
- **Path Traversal Prevention:** Never construct file paths directly from user input or filenames. Use secure path resolution and sanitized identifiers.
- **XSS & Markup Injection:** HTML report generation must escape all dataset values, column names, and findings using Jinja2 auto-escaping. Never insert raw strings into HTML templates.
- **No Dynamic Code Execution:** Never evaluate user input using `eval()`, `exec()`, or dynamic raw SQL queries.
- **Secrets:** Never log credentials, API keys, or machine environment variables. Never hardcode secrets.
- **Git Safety:** Do not commit broken tests, modify Git history, or commit directly to main without verification.

---

## 6. Task Execution Protocol for Coding Agents

When assigned a task from [`docs/implementation-plan.md`](file:///d:/Projects/lux-data-observability/docs/implementation-plan.md):
1. **Verify Prerequisites:** Ensure all prerequisite tasks have their status marked `COMPLETED` in [`docs/progress.md`](file:///d:/Projects/lux-data-observability/docs/progress.md).
2. **Review Task Scope:** Read the task's in-scope, out-of-scope, acceptance criteria, and edge cases.
3. **Check Code & Tests First:** Inspect relevant existing files.
4. **Implement Incrementally:** Keep changes minimal, targeted, and well-typed.
5. **Run Verification Commands:** Execute tests, linting, and type checking. Do not claim verification succeeded without actual terminal output.
6. **Update Progress:** Mark the task `COMPLETED` in [`docs/progress.md`](file:///d:/Projects/lux-data-observability/docs/progress.md) and record the completion summary and verification evidence.

