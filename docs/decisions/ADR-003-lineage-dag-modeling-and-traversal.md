# ADR-003: Explicit Lineage DAG Modeling and Traversal Strategy

## Status
Accepted

## Context
Lux requires an interactive, deterministic representation of data pipeline dependencies:
- Sources (raw files, tables).
- Transformations (SQL steps, ETL scripts, aggregations).
- Derived Datasets (staging tables, warehouse views).
- Metrics (KPIs, aggregated numbers).
- Downstream Reports (dashboards, automated emails, executive reports).

The lineage system must:
1. Validate declared dependencies against schema rules (detecting cycles, dangling references, isolated nodes).
2. Compute upstream origins for any given node.
3. Compute downstream impact trees when a quality validation fails.
4. Support interactive exploration in the web frontend.

We considered:
1. **Graph Database (Neo4j, ArangoDB):** High operational overhead, separate server container, unnecessary complexity for pipeline DAGs with tens to hundreds of nodes.
2. **Raw Relational Adjacency Table in SQLite:** Simple to persist, but complex and slow for recursive traversal (requiring recursive CTEs) and difficult to run cycle detection in memory.
3. **In-Memory NetworkX Graph with Relational Persistence:** In-memory graph model backed by NetworkX for graph algorithms (topological sort, cycles, upstream/downstream ancestor/descendant traversal), persisted in SQLite as typed nodes and edges.

## Decision
We chose an **In-Memory NetworkX Graph wrapped in a typed `LineageGraph` Domain Service**:
- **Domain Modeling:** Nodes and edges are defined as typed Pydantic models:
  - `LineageNode`: `id`, `name`, `type` (`SOURCE_DATASET`, `TRANSFORMATION`, `DERIVED_DATASET`, `METRIC`, `REPORT`), `status`, `metadata`.
  - `LineageEdge`: `id`, `source_id`, `target_id`, `transformation_type`, `contract_version`.
- **Encapsulated Graph Algorithms:** The `LineageGraph` class wraps `networkx.DiGraph`. It provides strict methods:
  - `add_node()`, `add_edge()`, `validate_dag()` (ensures acyclicity via `nx.is_directed_acyclic_graph`).
  - `get_upstream_path(node_id)` (`nx.ancestors`).
  - `get_downstream_impact(node_id)` (`nx.descendants` + BFS path extraction).
- **Validation Rules:** Graphs with cycles, missing node references, or unresolvable contracts are rejected with structured validation errors.
- **Frontend Visualization:** React Flow (`@xyflow/react`) is used on the client, receiving clean JSON representations with node coordinates auto-computed via Dagre layout algorithms.

## Consequences

### Positive
- **Algorithmic Reliability:** Uses battle-tested graph traversal and cycle detection algorithms.
- **No External Infrastructure:** Runs entirely in-memory with microsecond traversal speeds.
- **Clean API Contract:** Downstream impact traversal returns deterministic paths and clear explanation chains.

### Negative & Mitigations
- **Graph Size Limits:** In-memory graph representation could become heavy if graphs contain millions of nodes.
  - *Mitigation:* Observability pipeline graphs for single organizations/scenarios typically contain dozens to thousands of nodes, easily handled within tens of kilobytes of memory.

