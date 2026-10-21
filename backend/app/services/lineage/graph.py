"""Lineage DAG domain service encapsulating NetworkX DiGraph and graph integrity validator."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import networkx as nx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import CyclicDependencyError, LineageIntegrityError, NotFoundError
from app.models.lineage import (
    LineageEdge as DBLineageEdge,
)
from app.models.lineage import (
    LineageNode as DBLineageNode,
)
from app.schemas.lineage import (
    GraphValidationSummary,
    LineageEdge,
    LineageGraphSchema,
    LineageNode,
    LineageNodeType,
)


class LineageGraph:
    """Domain model representing an in-memory lineage Directed Acyclic Graph (DAG).

    Encapsulates NetworkX DiGraph to manage data pipeline nodes and dependency edges,
    enforcing DAG integrity constraints (cycle prevention, dangling reference detection,
    isolated node tracking) and providing graph traversal operations.
    """

    def __init__(
        self,
        scenario_id: str | None = None,
        name: str = "lineage_graph",
    ) -> None:
        self.scenario_id: str | None = scenario_id
        self.name: str = name
        self._graph: nx.DiGraph = nx.DiGraph(name=name)
        self._registered_nodes: set[str] = set()

    # -------------------------------------------------------------------------
    # Properties & Basic Queries
    # -------------------------------------------------------------------------

    @property
    def node_count(self) -> int:
        """Total number of nodes currently in graph."""
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        """Total number of edges currently in graph."""
        return self._graph.number_of_edges()

    @property
    def nodes(self) -> list[str]:
        """List of all node IDs currently in graph."""
        return list(self._graph.nodes)

    @property
    def edges(self) -> list[tuple[str, str]]:
        """List of all (source, target) edge tuples currently in graph."""
        return list(self._graph.edges)

    def has_node(self, node_id: str) -> bool:
        """Return True if node exists in the graph."""
        return node_id in self._graph

    def has_edge(self, source: str, target: str) -> bool:
        """Return True if a directed edge exists from source to target."""
        return self._graph.has_edge(source, target)

    # -------------------------------------------------------------------------
    # Node Management
    # -------------------------------------------------------------------------

    def add_node(
        self,
        node: LineageNode | dict[str, Any] | str,
        **attributes: Any,
    ) -> str:
        """Add a lineage node with metadata to the graph.

        Args:
            node: Either a LineageNode schema instance, a dictionary describing the node,
                  or a string node_id.
            **attributes: Additional node attributes if node is a string or dict.

        Returns:
            The string node identifier.
        """
        if isinstance(node, LineageNode):
            node_id = node.id
            node_data = node.model_dump()
        elif isinstance(node, dict):
            node_id = str(node.get("id") or node.get("node_id"))
            node_data = {**node, **attributes}
            node_data["id"] = node_id
            if "name" not in node_data:
                node_data["name"] = node_id
            if "type" not in node_data:
                node_data["type"] = LineageNodeType.DERIVED_DATASET.value
        elif isinstance(node, str):
            node_id = node
            node_data = {"id": node_id, "name": attributes.get("name", node_id), **attributes}
            if "type" not in node_data:
                node_data["type"] = LineageNodeType.DERIVED_DATASET.value
        else:
            raise TypeError(f"Unsupported node type: {type(node)}")

        # Ensure metadata is dictionary
        if "metadata" in node_data and isinstance(node_data["metadata"], str):
            try:
                node_data["metadata"] = json.loads(node_data["metadata"])
            except Exception:
                node_data["metadata"] = {}
        elif "metadata" not in node_data or node_data["metadata"] is None:
            node_data["metadata"] = {}

        self._registered_nodes.add(node_id)
        self._graph.add_node(node_id, **node_data)
        return node_id

    def add_nodes(self, nodes: Iterable[LineageNode | dict[str, Any] | str]) -> None:
        """Add multiple nodes to the graph."""
        for n in nodes:
            self.add_node(n)

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all incident edges from the graph."""
        if node_id in self._graph:
            self._graph.remove_node(node_id)
        self._registered_nodes.discard(node_id)

    def get_node(self, node_id: str) -> dict[str, Any]:
        """Get raw node attribute dictionary.

        Raises:
            NotFoundError: If node_id does not exist in graph.
        """
        if node_id not in self._graph:
            raise NotFoundError(
                code="NODE_NOT_FOUND",
                message=f"Lineage node '{node_id}' does not exist in graph.",
            )
        return dict(self._graph.nodes[node_id])

    def get_node_data(self, node_id: str) -> LineageNode:
        """Get node formatted as a typed LineageNode schema.

        Raises:
            NotFoundError: If node_id does not exist in graph.
        """
        data = self.get_node(node_id)
        return LineageNode(
            id=node_id,
            name=str(data.get("name", node_id)),
            type=str(data.get("type", LineageNodeType.DERIVED_DATASET.value)),
            dataset_id=data.get("dataset_id"),
            owner=data.get("owner"),
            description=data.get("description"),
            metadata=data.get("metadata", {}),
            execution_status=data.get("execution_status"),
            quality_health=data.get("quality_health"),
        )

    def get_all_nodes(self) -> list[LineageNode]:
        """Return all nodes in the graph as typed LineageNode models."""
        return [self.get_node_data(n) for n in self._graph.nodes]

    # -------------------------------------------------------------------------
    # Edge Management
    # -------------------------------------------------------------------------

    def add_edge(
        self,
        source: str,
        target: str,
        edge_id: str | None = None,
        dependency_type: str = "DIRECT_INPUT",
        validate_nodes: bool = False,
        **attributes: Any,
    ) -> str:
        """Add a directed dependency edge from source node to target node.

        Args:
            source: Source node ID.
            target: Target node ID.
            edge_id: Optional edge ID. Defaults to '{source}->{target}'.
            dependency_type: Link classification.
            validate_nodes: If True, raises LineageIntegrityError if source or target
                            is not an explicitly registered node.
            **attributes: Additional edge attributes.

        Returns:
            The edge identifier.
        """
        if validate_nodes:
            missing: list[str] = []
            if source not in self._registered_nodes:
                missing.append(source)
            if target not in self._registered_nodes:
                missing.append(target)
            if missing:
                raise LineageIntegrityError(
                    code="UNREGISTERED_NODE_REFERENCE",
                    message=(
                        f"Cannot add edge '{source}' -> '{target}': "
                        f"node(s) {missing} are not registered in the graph."
                    ),
                    details={"missing_nodes": missing, "source": source, "target": target},
                )

        actual_id = edge_id or f"{source}->{target}"
        edge_data = {
            "id": actual_id,
            "source": source,
            "target": target,
            "dependency_type": dependency_type,
            **attributes,
        }
        self._graph.add_edge(source, target, **edge_data)
        return actual_id

    def add_edges(
        self,
        edges: Iterable[LineageEdge | dict[str, Any] | tuple[str, str]],
        validate_nodes: bool = False,
    ) -> None:
        """Add multiple edges to the graph."""
        for e in edges:
            if isinstance(e, LineageEdge):
                self.add_edge(
                    source=e.source,
                    target=e.target,
                    edge_id=e.id,
                    dependency_type=e.dependency_type,
                    validate_nodes=validate_nodes,
                )
            elif isinstance(e, dict):
                src = str(e.get("source") or e.get("source_id"))
                tgt = str(e.get("target") or e.get("target_id"))
                eid = e.get("id")
                deptype = str(e.get("dependency_type", "DIRECT_INPUT"))
                skip_keys = {
                    "source",
                    "source_id",
                    "target",
                    "target_id",
                    "id",
                    "dependency_type",
                }
                attrs = {k: v for k, v in e.items() if k not in skip_keys}
                self.add_edge(
                    source=src,
                    target=tgt,
                    edge_id=eid,
                    dependency_type=deptype,
                    validate_nodes=validate_nodes,
                    **attrs,
                )
            elif isinstance(e, (tuple, list)) and len(e) >= 2:
                self.add_edge(source=e[0], target=e[1], validate_nodes=validate_nodes)

    def remove_edge(self, source: str, target: str) -> None:
        """Remove directed edge between source and target."""
        if self._graph.has_edge(source, target):
            self._graph.remove_edge(source, target)

    def get_edge(self, source: str, target: str) -> dict[str, Any]:
        """Get attributes of directed edge between source and target.

        Raises:
            NotFoundError: If edge does not exist.
        """
        if not self._graph.has_edge(source, target):
            raise NotFoundError(
                code="EDGE_NOT_FOUND",
                message=f"Lineage edge from '{source}' to '{target}' does not exist.",
            )
        return dict(self._graph.edges[source, target])

    def get_all_edges(self) -> list[LineageEdge]:
        """Return all edges formatted as typed LineageEdge models."""
        edge_list: list[LineageEdge] = []
        for u, v in self._graph.edges:
            data = self._graph.edges[u, v]
            edge_list.append(
                LineageEdge(
                    id=data.get("id", f"{u}->{v}"),
                    source=u,
                    target=v,
                    dependency_type=str(data.get("dependency_type", "DIRECT_INPUT")),
                )
            )
        return edge_list

    # -------------------------------------------------------------------------
    # Graph Integrity Validation
    # -------------------------------------------------------------------------

    def validate_integrity(self, allow_isolated: bool = True) -> GraphValidationSummary:
        """Inspect graph for structural integrity defects without raising exceptions.

        Checks:
        1. Directed Acyclic Graph (DAG) cycle detection.
        2. Dangling edge references (edges pointing to nodes not explicitly registered).
        3. Isolated nodes (nodes with in-degree 0 and out-degree 0).

        Args:
            allow_isolated: Whether isolated nodes are considered acceptable (warning only)
                            or fatal errors.

        Returns:
            GraphValidationSummary with complete integrity report.
        """
        errors: list[str] = []
        warnings: list[str] = []

        # 1. Cycle Detection
        is_dag = nx.is_directed_acyclic_graph(self._graph)
        cycles: list[list[str]] = []
        if not is_dag:
            # Extract simple cycles
            raw_cycles = list(nx.simple_cycles(self._graph))
            for c in raw_cycles:
                # Append first node at end to explicitly represent cycle loop path
                closed_cycle = list(c) + [c[0]]
                cycles.append(closed_cycle)
                errors.append(f"Cyclic dependency detected: {' -> '.join(closed_cycle)}")

        # 2. Dangling Edge References
        dangling_edges: list[dict[str, str]] = []
        for u, v in self._graph.edges:
            if u not in self._registered_nodes or v not in self._registered_nodes:
                dangling_edges.append({"source": u, "target": v})
                missing = [n for n in (u, v) if n not in self._registered_nodes]
                errors.append(
                    f"Dangling edge '{u}->{v}' references unregistered node(s): {missing}"
                )

        # 3. Isolated Nodes
        isolated_nodes = list(nx.isolates(self._graph))
        if isolated_nodes:
            msg = f"Graph contains {len(isolated_nodes)} isolated node(s): {isolated_nodes}"
            if not allow_isolated:
                errors.append(msg)
            else:
                warnings.append(msg)

        is_valid = len(errors) == 0

        return GraphValidationSummary(
            is_valid=is_valid,
            node_count=self.node_count,
            edge_count=self.edge_count,
            is_dag=is_dag,
            cycles=cycles,
            dangling_edges=dangling_edges,
            isolated_nodes=isolated_nodes,
            errors=errors,
            warnings=warnings,
        )

    def validate(self, allow_isolated: bool = True) -> None:
        """Validate graph integrity and raise structured exception on failure.

        Raises:
            CyclicDependencyError: If any directed cycle exists in the graph.
            LineageIntegrityError: If dangling edge references or other defects exist.
        """
        summary = self.validate_integrity(allow_isolated=allow_isolated)
        if not summary.is_valid:
            if summary.cycles:
                primary_cycle = summary.cycles[0]
                raise CyclicDependencyError(
                    message=(
                        f"Lineage graph contains cyclic dependencies: {' -> '.join(primary_cycle)}"
                    ),
                    cycle_path=primary_cycle,
                    details={"cycles": summary.cycles, "total_cycles": len(summary.cycles)},
                )
            if summary.dangling_edges:
                raise LineageIntegrityError(
                    code="DANGLING_EDGE_REFERENCE",
                    message=(
                        f"Lineage graph contains {len(summary.dangling_edges)} dangling edge "
                        f"reference(s) to unregistered nodes."
                    ),
                    details={"dangling_edges": summary.dangling_edges},
                )
            raise LineageIntegrityError(
                code="LINEAGE_INTEGRITY_ERROR",
                message="; ".join(summary.errors),
                details={"errors": summary.errors},
            )

    # -------------------------------------------------------------------------
    # Traversal & Dependency Queries
    # -------------------------------------------------------------------------

    def get_upstream_nodes(self, node_id: str, include_self: bool = False) -> set[str]:
        """Return all transitive upstream ancestor node IDs that feed into node_id.

        Args:
            node_id: Target node ID.
            include_self: If True, include node_id in the returned set.

        Returns:
            Set of ancestor node IDs.

        Raises:
            NotFoundError: If node_id is not in the graph.
        """
        if node_id not in self._graph:
            raise NotFoundError(
                code="NODE_NOT_FOUND",
                message=f"Node '{node_id}' does not exist in graph.",
            )
        ancestors: set[str] = set(nx.ancestors(self._graph, node_id))
        if include_self:
            ancestors.add(node_id)
        return ancestors

    def get_downstream_nodes(self, node_id: str, include_self: bool = False) -> set[str]:
        """Return all transitive downstream descendant node IDs that consume node_id.

        Args:
            node_id: Target node ID.
            include_self: If True, include node_id in the returned set.

        Returns:
            Set of descendant node IDs.

        Raises:
            NotFoundError: If node_id is not in the graph.
        """
        if node_id not in self._graph:
            raise NotFoundError(
                code="NODE_NOT_FOUND",
                message=f"Node '{node_id}' does not exist in graph.",
            )
        descendants: set[str] = set(nx.descendants(self._graph, node_id))
        if include_self:
            descendants.add(node_id)
        return descendants

    def get_upstream_dataset_ids(self, node_id: str, include_self: bool = False) -> set[str]:
        """Return all dataset IDs associated with upstream nodes feeding into node_id.

        Useful for determining which underlying storage datasets or CSV files
        affect a given downstream metric or report.
        """
        upstream_nodes = self.get_upstream_nodes(node_id, include_self=include_self)
        dataset_ids: set[str] = set()
        for nid in upstream_nodes:
            node_data = self.get_node(nid)
            ds_id = node_data.get("dataset_id")
            if ds_id:
                dataset_ids.add(str(ds_id))
        return dataset_ids

    def get_direct_upstream(self, node_id: str) -> list[str]:
        """Return immediate incoming predecessor node IDs."""
        if node_id not in self._graph:
            raise NotFoundError(
                code="NODE_NOT_FOUND",
                message=f"Node '{node_id}' does not exist in graph.",
            )
        return list(self._graph.predecessors(node_id))

    def get_direct_downstream(self, node_id: str) -> list[str]:
        """Return immediate outgoing successor node IDs."""
        if node_id not in self._graph:
            raise NotFoundError(
                code="NODE_NOT_FOUND",
                message=f"Node '{node_id}' does not exist in graph.",
            )
        return list(self._graph.successors(node_id))

    def topological_sort(self) -> list[str]:
        """Return a topologically sorted list of node IDs.

        Nodes appear in execution/dependency order: dependencies precede consumers.

        Raises:
            CyclicDependencyError: If the graph contains a cycle.
        """
        if not nx.is_directed_acyclic_graph(self._graph):
            raw_cycles = list(nx.simple_cycles(self._graph))
            primary_cycle = (list(raw_cycles[0]) + [raw_cycles[0][0]]) if raw_cycles else []
            raise CyclicDependencyError(
                message=(
                    f"Cannot perform topological sort on cyclic graph: {' -> '.join(primary_cycle)}"
                ),
                cycle_path=primary_cycle,
                details={"cycles": raw_cycles},
            )
        return list(nx.topological_sort(self._graph))

    def has_path(self, source: str, target: str) -> bool:
        """Return True if a directed path exists from source to target."""
        if source not in self._graph or target not in self._graph:
            return False
        return nx.has_path(self._graph, source, target)

    def get_shortest_path(self, source: str, target: str) -> list[str]:
        """Return shortest directed path from source to target as list of node IDs.

        Returns empty list if no path exists.
        """
        if source not in self._graph or target not in self._graph:
            return []
        try:
            return list(nx.shortest_path(self._graph, source, target))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_all_paths(self, source: str, target: str) -> list[list[str]]:
        """Return all simple paths from source to target."""
        if source not in self._graph or target not in self._graph:
            return []
        return [list(p) for p in nx.all_simple_paths(self._graph, source, target)]

    def get_root_nodes(self) -> list[str]:
        """Return all source/origin nodes (in-degree == 0)."""
        return [n for n in self._graph.nodes if self._graph.in_degree(n) == 0]

    def get_terminal_nodes(self) -> list[str]:
        """Return all leaf/consumer nodes (out-degree == 0)."""
        return [n for n in self._graph.nodes if self._graph.out_degree(n) == 0]

    def get_isolated_nodes(self) -> list[str]:
        """Return all nodes having zero incoming and zero outgoing edges."""
        return list(nx.isolates(self._graph))

    def get_subgraph(self, node_ids: Iterable[str]) -> LineageGraph:
        """Return a new LineageGraph containing the induced subgraph over node_ids."""
        sub = LineageGraph(scenario_id=self.scenario_id, name=f"{self.name}_subgraph")
        valid_nodes = [n for n in node_ids if n in self._graph]
        for nid in valid_nodes:
            sub.add_node(self.get_node(nid))
        for u, v in self._graph.edges:
            if u in valid_nodes and v in valid_nodes:
                edge_attrs = dict(self._graph.edges[u, v])
                eid = edge_attrs.pop("id", None)
                deptype = edge_attrs.pop("dependency_type", "DIRECT_INPUT")
                edge_attrs.pop("source", None)
                edge_attrs.pop("target", None)
                sub.add_edge(
                    source=u,
                    target=v,
                    edge_id=eid,
                    dependency_type=deptype,
                    **edge_attrs,
                )
        return sub

    # -------------------------------------------------------------------------
    # Serialization & Seed Factory Loaders
    # -------------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize graph to dictionary conforming to scenario schema."""
        return {
            "scenario_id": self.scenario_id,
            "nodes": [n.model_dump() for n in self.get_all_nodes()],
            "edges": [e.model_dump() for e in self.get_all_edges()],
        }

    def to_schema(self) -> LineageGraphSchema:
        """Serialize graph to typed LineageGraphSchema."""
        return LineageGraphSchema(
            scenario_id=self.scenario_id,
            nodes=self.get_all_nodes(),
            edges=self.get_all_edges(),
        )

    @classmethod
    def from_scenario_dict(
        cls,
        data: dict[str, Any],
        scenario_id: str | None = None,
        validate: bool = True,
    ) -> LineageGraph:
        """Construct a LineageGraph instance from scenario dictionary metadata.

        Accepts either full scenario dictionary containing a 'lineage' key,
        or direct lineage dictionary containing 'nodes' and 'edges'.

        Args:
            data: Scenario or lineage dictionary.
            scenario_id: Optional scenario ID override.
            validate: If True, validates graph integrity and raises if cyclic or defective.
        """
        lineage_data = data.get("lineage", data)
        effective_scenario_id = scenario_id or data.get("id") or lineage_data.get("scenario_id")

        graph = cls(
            scenario_id=str(effective_scenario_id) if effective_scenario_id else None,
            name=f"lineage_{effective_scenario_id or 'default'}",
        )

        # Ingest nodes first
        nodes = lineage_data.get("nodes", [])
        for node_def in nodes:
            graph.add_node(node_def)

        # Ingest edges
        edges = lineage_data.get("edges", [])
        for edge_def in edges:
            src = edge_def.get("source") or edge_def.get("source_id")
            tgt = edge_def.get("target") or edge_def.get("target_id")
            if src and tgt:
                eid = edge_def.get("id") or f"{src}->{tgt}"
                deptype = edge_def.get("dependency_type", "DIRECT_INPUT")
                graph.add_edge(source=src, target=tgt, edge_id=eid, dependency_type=deptype)

        if validate:
            graph.validate()

        return graph

    @classmethod
    def from_scenario_file(
        cls,
        path: str | Path,
        scenario_id: str | None = None,
        validate: bool = True,
    ) -> LineageGraph:
        """Construct a LineageGraph instance from a scenario.json file on disk."""
        file_path = Path(path)
        if not file_path.exists():
            raise NotFoundError(
                code="SCENARIO_FILE_NOT_FOUND",
                message=f"Lineage scenario file not found at: {file_path}",
            )
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_scenario_dict(data, scenario_id=scenario_id, validate=validate)

    @classmethod
    def from_db(
        cls,
        db: Session,
        scenario_id: str,
        validate: bool = True,
    ) -> LineageGraph:
        """Construct a LineageGraph by querying lineage nodes and edges from SQLite database.

        Args:
            db: Active SQLAlchemy database session.
            scenario_id: Target scenario ID.
            validate: If True, validates graph integrity on load.

        Raises:
            NotFoundError: If no lineage nodes are registered for the given scenario.
        """
        stmt_nodes = select(DBLineageNode).where(DBLineageNode.scenario_id == scenario_id)
        db_nodes = db.execute(stmt_nodes).scalars().all()

        if not db_nodes:
            raise NotFoundError(
                code="LINEAGE_NOT_FOUND",
                message=f"No lineage records found in database for scenario '{scenario_id}'.",
            )

        graph = cls(scenario_id=scenario_id, name=f"lineage_{scenario_id}")

        for n in db_nodes:
            metadata_dict: dict[str, Any] = {}
            if n.node_metadata:
                try:
                    metadata_dict = json.loads(n.node_metadata)
                except Exception:
                    metadata_dict = {}

            graph.add_node(
                LineageNode(
                    id=n.id,
                    name=n.name,
                    type=n.node_type,
                    dataset_id=n.dataset_id,
                    owner=n.owner,
                    description=n.description,
                    metadata=metadata_dict,
                )
            )

        stmt_edges = select(DBLineageEdge).where(DBLineageEdge.scenario_id == scenario_id)
        db_edges = db.execute(stmt_edges).scalars().all()

        for e in db_edges:
            graph.add_edge(
                source=e.source_id,
                target=e.target_id,
                edge_id=e.id,
                dependency_type=e.dependency_type,
            )

        if validate:
            graph.validate()

        return graph
