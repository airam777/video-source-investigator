"""Deterministic incremental registry for immutable evidence records.

The registry is a local in-memory builder. It performs no I/O and never mutates
registered evidence objects. A validated immutable graph is produced by build().
"""
from __future__ import annotations

from .evidence_model import (
    EvidenceGraphContainer,
    EvidenceObservation,
    EvidenceRelation,
)


class EvidenceRegistry:
    """Collect observations and relations before producing a validated graph.

    Re-registering an identical record is idempotent. Reusing an ID for a
    different record is rejected, preventing silent identity collisions.
    Referential integrity is checked when build() creates the graph, so records
    may be registered in any order.
    """

    MAX_OBSERVATIONS = 10_000
    MAX_RELATIONS = 20_000

    def __init__(self) -> None:
        self._observations: dict[str, EvidenceObservation] = {}
        self._relations: dict[str, EvidenceRelation] = {}

    def register_observation(self, observation: EvidenceObservation) -> bool:
        """Register an observation; return False when an identical ID exists."""
        if not isinstance(observation, EvidenceObservation):
            raise TypeError("observation must be an EvidenceObservation.")
        existing = self._observations.get(observation.observation_id)
        if existing is not None:
            if existing == observation:
                return False
            raise ValueError("Conflicting observation ID already registered.")
        if len(self._observations) >= self.MAX_OBSERVATIONS:
            raise ValueError("Evidence registry observation limit exceeded.")
        self._observations[observation.observation_id] = observation
        return True

    def register_relation(self, relation: EvidenceRelation) -> bool:
        """Register a relation; endpoint validation is deferred until build()."""
        if not isinstance(relation, EvidenceRelation):
            raise TypeError("relation must be an EvidenceRelation.")
        existing = self._relations.get(relation.relation_id)
        if existing is not None:
            if existing == relation:
                return False
            raise ValueError("Conflicting relation ID already registered.")
        if len(self._relations) >= self.MAX_RELATIONS:
            raise ValueError("Evidence registry relation limit exceeded.")
        self._relations[relation.relation_id] = relation
        return True

    def register_graph(self, graph: EvidenceGraphContainer) -> tuple[int, int]:
        """Atomically add a validated graph; return new observation/relation counts."""
        if not isinstance(graph, EvidenceGraphContainer):
            raise TypeError("graph must be an EvidenceGraphContainer.")

        observations = self._observations.copy()
        relations = self._relations.copy()

        for observation in graph.observations:
            existing = observations.get(observation.observation_id)
            if existing is not None and existing != observation:
                raise ValueError("Conflicting observation ID already registered.")
            observations[observation.observation_id] = observation

        for relation in graph.relations:
            existing = relations.get(relation.relation_id)
            if existing is not None and existing != relation:
                raise ValueError("Conflicting relation ID already registered.")
            relations[relation.relation_id] = relation

        if len(observations) > self.MAX_OBSERVATIONS:
            raise ValueError("Evidence registry observation limit exceeded.")
        if len(relations) > self.MAX_RELATIONS:
            raise ValueError("Evidence registry relation limit exceeded.")

        # Validate cross-graph references and graph invariants before committing.
        EvidenceGraphContainer(
            observations=tuple(observations.values()),
            relations=tuple(relations.values()),
        )

        added_observations = len(observations) - len(self._observations)
        added_relations = len(relations) - len(self._relations)
        self._observations = observations
        self._relations = relations
        return added_observations, added_relations

    def build(self) -> EvidenceGraphContainer:
        """Return a new immutable graph in deterministic ID order."""
        return EvidenceGraphContainer(
            observations=tuple(
                self._observations[key] for key in sorted(self._observations)
            ),
            relations=tuple(
                self._relations[key] for key in sorted(self._relations)
            ),
        )

    @property
    def observation_count(self) -> int:
        return len(self._observations)

    @property
    def relation_count(self) -> int:
        return len(self._relations)
