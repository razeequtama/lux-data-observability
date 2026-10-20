# ADR-001: Modular Monolith Architecture using FastAPI and React

## Status
Accepted

## Context
Lux is a data observability platform designed for investigating data reliability failures, tracing lineage, monitoring pipeline history, and verifying recovery. The application must support reproducible bundled scenarios and local dataset uploads without requiring paid external services, distributed message brokers, or external cloud infrastructure. It must be accessible for developers, data engineers, and evaluators running on a single laptop or containerized environment.

We considered three primary architecture styles:
1. **Distributed Microservices:** Separate services for Ingestion, Validation, Lineage, Pipeline Observability, and Reports, communicating over gRPC/Kafka.
2. **Modular Monolith (FastAPI + React/TypeScript SPA):** A cohesive backend with strictly isolated domain packages, backed by a fast modern frontend SPA, packaged together via Docker Compose.
3. **Server-Side Rendered Monolith (Django / Flask + Jinja/HTMX):** A single Python process rendering HTML server-side.

## Decision
We chose the **Modular Monolith** architecture:
- **Backend:** Python 3.13 with FastAPI and Pydantic v2.
  - Clear internal module boundaries: Ingestion, Validation Engine, Lineage DAG, Impact Analysis, Pipeline Observability, and Report Generation.
  - Strict dependency rules: Services communicate through typed Python interfaces and Pydantic schemas, not direct cross-module database manipulation.
- **Frontend:** React 18+ with TypeScript and Vite.
  - Provides a rich, interactive UI for complex DAG exploration (via React Flow), filtering multi-attribute validation findings, and exploring multi-step impact paths.
- **Packaging:** Docker Compose orchestrating the FastAPI backend, static Vite frontend server (or reverse proxy), and local persistent volume for SQLite and report artifacts.

## Consequences

### Positive
- **Low Operational Overhead:** No microservice orchestration, network serialization penalties, or message broker maintenance.
- **Fast Local Feedback:** Developers and evaluators can run the entire platform with one `docker compose up` command or local dev servers.
- **Rich Interactive Visualizations:** React enables high-performance SVG/Canvas DAG rendering for data lineage and responsive UI filtering across hundreds of validation findings.
- **Strict Boundary Enforcement:** Domain services can be developed, tested, and refactored in complete isolation with deterministic unit tests.

### Negative & Mitigations
- **Shared Process Resources:** Validation engine workloads run in the same Python application runtime as the web API.
  - *Mitigation:* Heavy validations run in worker threads or process pools; dataset uploads are capped at 20MB with streaming/chunked processing to prevent event-loop starvation.
- **Frontend/Backend Contract Drift:** Risk of mismatch between FastAPI response models and TypeScript interfaces.
  - *Mitigation:* Pydantic schemas serve as the single source of truth, with OpenAPI specs checked in CI.

