"""Canonical graph representation and relationships."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Sequence

from aip_canonica.models.base import CanonicalNode


@dataclass(frozen=True, slots=True)
class Relationship:
    """A directed relationship between two canonical nodes.

    Attributes:
        source_id: Identity of the originating node.
        relation: Type of relation (e.g. 'account', 'holder', 'contains', 'counterparty').
        target_id: Identity of the target node.
        target_type: Expected node type of the target (e.g. 'Party', 'Account').
        properties: Additional metadata or attributes for the edge.
    """

    source_id: str
    relation: str
    target_id: str
    target_type: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize relationship to dictionary format."""
        data: dict[str, Any] = {
            "source_id": self.source_id,
            "relation": self.relation,
            "target_id": self.target_id,
        }
        if self.target_type is not None:
            data["target_type"] = self.target_type
        if self.properties:
            data["properties"] = self.properties
        return data


class CanonicalGraph:
    """Graph structure connecting canonical financial nodes via directed relationships."""

    def __init__(
        self,
        nodes: Sequence[CanonicalNode] | None = None,
        relationships: Sequence[Relationship] | None = None,
    ) -> None:
        """Initialize graph with nodes and relationships.

        Args:
            nodes: Collection of canonical nodes to add to the graph.
            relationships: Collection of relationships to add to the graph.
        """
        self._nodes: dict[str, CanonicalNode] = {}
        self._outgoing: dict[str, list[Relationship]] = defaultdict(list)
        self._incoming: dict[str, list[Relationship]] = defaultdict(list)
        self._relationships: list[Relationship] = []

        if nodes:
            for node in nodes:
                self.add_node(node)
        if relationships:
            for rel in relationships:
                self.add_relationship(rel)

    def add_node(self, node: CanonicalNode) -> None:
        """Register a node into the graph.

        Note: If a node with the same ID already exists, it will be replaced.
        """
        self._nodes[node.id] = node

    def add_relationship(self, relationship: Relationship) -> None:
        """Register a directed relationship into the graph."""
        self._relationships.append(relationship)
        self._outgoing[relationship.source_id].append(relationship)
        self._incoming[relationship.target_id].append(relationship)

    def get_node(self, node_id: str) -> CanonicalNode | None:
        """Retrieve a node by its identity, or None if not found."""
        return self._nodes.get(node_id)

    def outgoing(
        self, node_id: str, relation: str | None = None
    ) -> list[Relationship]:
        """Discover all outgoing relationships from node_id.

        Args:
            node_id: ID of the node to query.
            relation: Optional filter for relationship type.

        Returns:
            List of relationships matching the criteria.
        """
        rels = self._outgoing.get(node_id, [])
        if relation is not None:
            return [r for r in rels if r.relation == relation]
        return rels

    def incoming(
        self, node_id: str, relation: str | None = None
    ) -> list[Relationship]:
        """Discover all incoming relationships to node_id.

        Args:
            node_id: ID of the node to query.
            relation: Optional filter for relationship type.

        Returns:
            List of relationships matching the criteria.
        """
        rels = self._incoming.get(node_id, [])
        if relation is not None:
            return [r for r in rels if r.relation == relation]
        return rels

    def target_nodes(
        self, node_id: str, relation: str | None = None
    ) -> list[CanonicalNode]:
        """Retrieve resolved target nodes along outgoing relationships.

        Returns only nodes that exist in the graph.
        """
        results: list[CanonicalNode] = []
        for r in self.outgoing(node_id, relation):
            target = self.get_node(r.target_id)
            if target is not None:
                results.append(target)
        return results

    def source_nodes(
        self, node_id: str, relation: str | None = None
    ) -> list[CanonicalNode]:
        """Retrieve resolved source nodes along incoming relationships.

        Returns only nodes that exist in the graph.
        """
        results: list[CanonicalNode] = []
        for r in self.incoming(node_id, relation):
            source = self.get_node(r.source_id)
            if source is not None:
                results.append(source)
        return results

    @property
    def nodes(self) -> list[CanonicalNode]:
        """All registered nodes in the graph."""
        return list(self._nodes.values())

    @property
    def relationships(self) -> list[Relationship]:
        """All registered relationships in the graph."""
        return list(self._relationships)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the graph to standard dictionary format."""
        return {
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "relationships": [rel.to_dict() for rel in self._relationships],
        }