# ADR-004: Persistence Strategy — SQLite with WAL Mode and Local Artifact Directory

## Status
Accepted

## Context
Lux requires persistent storage for:
1. Scenario configurations and dataset descriptors.
2. Historical validation runs and granular findings evidence.
3. Pipeline execution runs, step logs, record counts, and freshness checkpoints.
4. Lineage node and edge definitions.
5. Investigations and generated incident reports (JSON and HTML).

The persistence layer must:
- Persist across container and application restarts.
- Operate locally without requiring paid cloud databases or complex database servers.
- Handle concurrent read operations while validations write findings.
- Safely isolate uploaded datasets and generated report artifacts.

## Decision
We chose **SQLite with WAL (Write-Ahead Logging) Mode combined with an Isolated Filesystem Artifact Store**:
- **Relational Metadata Database:**
  - SQLite database file located at `data/lux.db`.
  - Configured with `PRAGMA journal_mode=WAL;` and `PRAGMA busy_timeout=5000;` to enable non-blocking concurrent readers while writes execute.
  - Managed via **SQLAlchemy 2.0** ORM and **Alembic** for schema migrations.
  - Foreign key constraints enabled via `PRAGMA foreign_keys=ON;`.
- **Artifact & File Storage:**
  - Raw scenario datasets, uploaded files, and generated HTML/JSON reports are stored in dedicated filesystem subdirectories:
    - `data/scenarios/`: Read-only bundled scenarios and fixtures.
    - `data/uploads/`: User-uploaded datasets, isolated with unique UUID directories.
    - `data/artifacts/`: Generated immutable incident reports.
  - Files are referenced in SQLite by relative path and SHA-256 checksums to ensure file integrity.

## Consequences

### Positive
- **Zero Configuration:** Runs immediately on any host or container without deploying or configuring database server containers.
- **Transactional Integrity:** SQLite provides full ACID compliance for metadata, run histories, and validation findings.
- **File Portability:** The entire state (`lux.db` and artifacts) can be backed up or reset simply by managing the `data/` directory.

### Negative & Mitigations
- **Write Concurrency Limits:** SQLite supports a single active writer at a time.
  - *Mitigation:* Observability validation runs write sequentially per job; WAL mode prevents read queries from blocking on write transactions.
- **Path Traversal Risk:** Storing files on disk requires strict path sanitization.
  - *Mitigation:* All file paths are generated via UUIDv4 namespaces within the `data/` root and validated with canonical path boundary checks before any disk I/O.

