import unittest
from core.evidence_model import EvidenceGraphContainer, EvidenceObservation, EvidenceRelation, NormalizedValue, RelationType
DIGEST = "a" * 64
def obs(oid): return EvidenceObservation(oid, "html_title", NormalizedValue("string", "Example"), DIGEST, "head.title")
class EvidenceModelTests(unittest.TestCase):
    def test_observation_confidence_validation(self):
        with self.assertRaises(ValueError): EvidenceObservation("obs-1", "title", NormalizedValue("string", "x"), DIGEST, "title", detector_confidence=float("nan"))
        with self.assertRaises(ValueError): EvidenceObservation("obs-1", "title", NormalizedValue("string", "x"), DIGEST, "title", detector_confidence=1.1)
    def test_graph_rejects_duplicate_and_missing_references(self):
        with self.assertRaises(ValueError): EvidenceGraphContainer((obs("obs-1"), obs("obs-1")))
        edge = EvidenceRelation("rel-1", RelationType.RELATED_TO, "obs-1", "missing", ("obs-1",))
        with self.assertRaises(ValueError): EvidenceGraphContainer((obs("obs-1"),), (edge,))
    def test_derived_from_cycle_rejected(self):
        edges = (EvidenceRelation("r1", RelationType.DERIVED_FROM, "obs-1", "obs-2", ("obs-1",)), EvidenceRelation("r2", RelationType.DERIVED_FROM, "obs-2", "obs-1", ("obs-2",)))
        with self.assertRaises(ValueError): EvidenceGraphContainer((obs("obs-1"), obs("obs-2")), edges)
    def test_related_to_cycles_are_permitted(self):
        edges = (EvidenceRelation("r1", RelationType.RELATED_TO, "obs-1", "obs-2", ("obs-1",)), EvidenceRelation("r2", RelationType.RELATED_TO, "obs-2", "obs-1", ("obs-2",)))
        self.assertEqual(len(EvidenceGraphContainer((obs("obs-1"), obs("obs-2")), edges).relations), 2)
    def test_value_is_nested_immutable(self):
        value = NormalizedValue("object", {"items": ["a"]})
        with self.assertRaises(TypeError): value.value["new"] = 1
        with self.assertRaises(AttributeError): value.value["items"].append("b")
if __name__ == "__main__": unittest.main()
