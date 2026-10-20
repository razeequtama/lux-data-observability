# Lux — Data Observability Platform

> **Lux** is a data observability platform for data quality validation, lineage tracking, pipeline monitoring, and downstream impact analysis.

---

## Overview

When datasets become corrupted, pipelines produce suspicious output, or business reports show conflicting numbers, data teams need an objective, evidence-based investigation tool to answer:
- **What failed?**
- **What evidence supports the finding?**
- **Where in the pipeline did the problem originate?**
- **Which downstream datasets, metrics, and executive reports are affected?**
- **Did the pipeline fail mechanically, or did it execute successfully with exit code 0 while producing corrupted data?**
- **What must be verified before downstream outputs can be trusted again?**

Lux provides a reproducible, end-to-end investigation workflow: **Trace the Failure**.

---

## Core Workflow: Trace the Failure

```text
[1. Load Scenario] ➔ [2. Execute Validations] ➔ [3. Inspect Findings & Evidence] ➔ [4. Trace Lineage DAG]
                                                                                          │
[8. Verify Recovery]  [7. Export Incident Report]  [6. Inspect Pipeline History]  [5. Trace Downstream Impact]
```

---

## Documentation Index

Comprehensive technical architecture, specifications, and project plans are located in the `docs/` directory:

- [**Product Requirements Document (PRD)**](file:///d:/Projects/lux-data-observability/docs/product-requirements.md): Functional requirements (FR-01 through FR-09), signature scenario (*Monday Revenue Mystery*), personas, and accessibility standards.
- [**System Architecture**](file:///d:/Projects/lux-data-observability/docs/architecture.md): Modular monolith design, service boundaries, data flow, and frontend hierarchy.
- [**Data Model & Schemas**](file:///d:/Projects/lux-data-observability/docs/data-model.md): Entity relationship model, SQLite schema DDL, scenario metadata schemas, and status vocabularies.
- [**REST API Contracts**](file:///d:/Projects/lux-data-observability/docs/api-contracts.md): Complete OpenAPI-aligned endpoint specifications and JSON envelopes.
- [**Security & Trust Boundaries**](file:///d:/Projects/lux-data-observability/docs/security.md): Threat modeling, input sanitization, path traversal defenses, and report XSS prevention.
- [**Testing Strategy & Quality Assurance**](file:///d:/Projects/lux-data-observability/docs/testing-strategy.md): Testing pyramid, coverage targets, unit/integration suites, and E2E acceptance tests.
- [**Implementation Backlog & Task Specifications**](file:///d:/Projects/lux-data-observability/docs/implementation-plan.md): Dependency-aware tasks (`T01`–`T24`) with strict Definition of Ready and Definition of Done.
- [**Live Progress Tracker**](file:///d:/Projects/lux-data-observability/docs/progress.md): Implementation status across milestones and tasks.
- [**Architecture Decision Records (ADRs)**](file:///d:/Projects/lux-data-observability/docs/decisions/):
  - [ADR-001: Modular Monolith Architecture (FastAPI + React)](file:///d:/Projects/lux-data-observability/docs/decisions/ADR-001-modular-monolith-fastapi-react.md)
  - [ADR-002: Deterministic Custom Python Validation Engine](file:///d:/Projects/lux-data-observability/docs/decisions/ADR-002-deterministic-python-validation-engine.md)
  - [ADR-003: Explicit Lineage DAG Modeling & NetworkX Traversal](file:///d:/Projects/lux-data-observability/docs/decisions/ADR-003-lineage-dag-modeling-and-traversal.md)
  - [ADR-004: Persistence Strategy: SQLite with WAL & Local Artifacts](file:///d:/Projects/lux-data-observability/docs/decisions/ADR-004-persistence-sqlite-wal-and-local-artifacts.md)
  - [ADR-005: Safe Incident Report Generation & XSS Sanitization](file:///d:/Projects/lux-data-observability/docs/decisions/ADR-005-safe-html-report-generation-and-sanitization.md)
  - [ADR-006: Separation of Pipeline Execution Health & Data Quality Health](file:///d:/Projects/lux-data-observability/docs/decisions/ADR-006-separation-of-pipeline-health-and-data-quality.md)
- [**Agent Guidelines (AGENTS.md)**](file:///d:/Projects/lux-data-observability/AGENTS.md): Operational instructions, verification commands, and execution protocols for coding agents.

---

## Technology Stack

- **Backend:** Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0, NetworkX, Jinja2
- **Frontend:** React 18+, TypeScript, Vite, Tailwind CSS, React Flow (`@xyflow/react`), Lucide React
- **Persistence & Storage:** SQLite (WAL mode) + local filesystem artifact store
- **Containerization:** Docker Compose
- **Testing:** Pytest (Backend) + Vitest / React Testing Library (Frontend)

