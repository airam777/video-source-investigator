import unittest
from core.identity import compute_observation_id
class DeterministicIdTests(unittest.TestCase):
    def test_stable_and_sensitive_to_occurrence(self):
        digest = "a" * 64
        a = compute_observation_id(digest, "meta", "head.title", {"value": "hello"})
        b = compute_observation_id(digest, "meta", "head.title", {"value": "hello"})
        c = compute_observation_id(digest, "meta", "head.title", {"value": "hello"}, 1)
        self.assertEqual(a, b); self.assertNotEqual(a, c)
    def test_rejects_too_small_byte_budget(self):
        with self.assertRaises(ValueError): compute_observation_id("a" * 64, "meta", "x", {"v": "x"}, max_byte_budget=10)
    def test_rejects_boolean_occurrence_index(self):
        with self.assertRaises(ValueError): compute_observation_id("a" * 64, "meta", "x", {}, True)
if __name__ == "__main__": unittest.main()
