import unittest

from core.evidence_model import (
    EvidenceGraphContainer,
    EvidenceObservation,
    EvidenceRelation,
    EvidenceStatus,
    NormalizedValue,
    RelationType,
)
from core.registry import EvidenceRegistry

DIGEST = "a" * 64


def observation(oid, value="Example"):
    return EvidenceObservation(
        observation_id=oid,
        kind="html_title",
        value=NormalizedValue("string", value),
        document_sha256=DIGEST,
        locator="head.title",
        evidence_status=EvidenceStatus.FACT,
    )


def relation(rid, source="obs-a", target="obs-b", sources=("obs-a",)):
    return EvidenceRelation(
        relation_id=rid,
        relation_type=RelationType.REFERENCES,
        source_id=source,
        target_id=target,
        source_observation_ids=sources,
    )


class EvidenceRegistryTests(unittest.TestCase):
    def test_registering_identical_records_is_idempotent(self):
        registry = EvidenceRegistry()
        item = observation("obs-a")
        self.assertTrue(registry.register_observation(item))
        self.assertFalse(registry.register_observation(item))
        self.assertEqual(registry.observation_count, 1)

    def test_conflicting_observation_identity_is_rejected(self):
        registry = EvidenceRegistry()
        registry.register_observation(observation("obs-a", "First"))
        with self.assertRaisesRegex(ValueError, "Conflicting observation ID"):
            registry.register_observation(observation("obs-a", "Different"))

    def test_conflicting_relation_identity_is_rejected(self):
        registry = EvidenceRegistry()
        registry.register_relation(relation("rel-a", target="obs-b"))
        with self.assertRaisesRegex(ValueError, "Conflicting relation ID"):
            registry.register_relation(relation("rel-a", target="obs-c"))

    def test_relations_can_be_registered_before_their_observations(self):
        registry = EvidenceRegistry()
        registry.register_relation(relation("rel-a"))
        registry.register_observation(observation("obs-b"))
        registry.register_observation(observation("obs-a"))
        graph = registry.build()
        self.assertEqual(len(graph.observations), 2)
        self.assertEqual(len(graph.relations), 1)

    def test_build_checks_referential_integrity(self):
        registry = EvidenceRegistry()
        registry.register_observation(observation("obs-a"))
        registry.register_relation(relation("rel-a"))
        with self.assertRaisesRegex(ValueError, "endpoint does not exist"):
            registry.build()

    def test_build_order_is_deterministic(self):
        first = EvidenceRegistry()
        second = EvidenceRegistry()
        for item in (observation("obs-z"), observation("obs-a"), observation("obs-m")):
            first.register_observation(item)
        for item in (observation("obs-m"), observation("obs-z"), observation("obs-a")):
            second.register_observation(item)
        self.assertEqual(
            [item.observation_id for item in first.build().observations],
            [item.observation_id for item in second.build().observations],
        )

    def test_register_graph_is_atomic_and_idempotent(self):
        source_graph = EvidenceGraphContainer(
            observations=(observation("obs-a"), observation("obs-b")),
            relations=(relation("rel-a"),),
        )
        registry = EvidenceRegistry()
        self.assertEqual(registry.register_graph(source_graph), (2, 1))
        self.assertEqual(registry.register_graph(source_graph), (0, 0))
        self.assertEqual(registry.observation_count, 2)
        self.assertEqual(registry.relation_count, 1)

    def test_register_graph_rejects_conflicts_without_partial_mutation(self):
        registry = EvidenceRegistry()
        registry.register_observation(observation("obs-a", "Existing"))
        incoming = EvidenceGraphContainer(
            observations=(observation("obs-b"), observation("obs-a", "Conflicting")),
        )
        with self.assertRaisesRegex(ValueError, "Conflicting observation ID"):
            registry.register_graph(incoming)
        self.assertEqual(registry.observation_count, 1)
        self.assertEqual(registry.build().observations[0].value.value, "Existing")

    def test_rejects_wrong_record_types(self):
        registry = EvidenceRegistry()
        with self.assertRaises(TypeError):
            registry.register_observation({})
        with self.assertRaises(TypeError):
            registry.register_relation({})
        with self.assertRaises(TypeError):
            registry.register_graph({})


if __name__ == "__main__":
    unittest.main()
