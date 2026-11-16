import unittest
from core.evidence_model import EvidenceGraphContainer, EvidenceObservation, EvidenceRelation, NormalizedValue, RelationType
DIGEST = "b" * 64
def observation(oid): return EvidenceObservation(oid, "host", NormalizedValue("string", "example.test"), DIGEST, "script[0].host")
class EvidenceRelationTests(unittest.TestCase):
    def test_derived_dag_is_accepted(self):
        edges = (EvidenceRelation("edge-a", RelationType.DERIVED_FROM, "node-a", "node-b", ("node-a",)), EvidenceRelation("edge-b", RelationType.DERIVED_FROM, "node-b", "node-c", ("node-b",)))
        self.assertEqual(len(EvidenceGraphContainer((observation("node-a"), observation("node-b"), observation("node-c")), edges).relations), 2)
    def test_relation_requires_observation_provenance(self):
        with self.assertRaises(ValueError): EvidenceRelation("edge-a", RelationType.REFERENCES, "node-a", "node-b", ())
    def test_relation_provenance_must_be_a_unique_collection(self):
        with self.assertRaises(ValueError): EvidenceRelation("edge-b", RelationType.REFERENCES, "node-a", "node-b", "node-a")
        with self.assertRaises(ValueError): EvidenceRelation("edge-c", RelationType.REFERENCES, "node-a", "node-b", ("node-a", "node-a"))
if __name__ == "__main__": unittest.main()
