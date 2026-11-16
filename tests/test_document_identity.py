import hashlib, unittest
from core.identity import DocumentIdentity, canonicalize_payload
from core.document_context import AnalysisContext
class DocumentIdentityTests(unittest.TestCase):
    def test_identity_from_bytes(self):
        raw = b"hello"; self.assertEqual(DocumentIdentity.from_bytes(raw).sha256, hashlib.sha256(raw).hexdigest()); self.assertEqual(DocumentIdentity.from_bytes(raw).size_bytes, 5)
    def test_rejects_invalid_identity(self):
        with self.assertRaises(ValueError): DocumentIdentity("A" * 64, 0)
        with self.assertRaises(ValueError): DocumentIdentity("a" * 64, True)
    def test_payload_normalizes_nfc_and_detects_collisions(self):
        self.assertEqual(canonicalize_payload({"e\\u0301": "e\\u0301"}), {"é": "é"})
        with self.assertRaises(ValueError): canonicalize_payload({"é": 1, "e\\u0301": 2})
    def test_aggregated_string_budget_boundary(self):
        exact = ["a" * 10000 for _ in range(51)] + ["b" * 2000]
        canonicalize_payload(exact, max_aggregated_string_bytes=512000)
        over = ["a" * 10000 for _ in range(51)] + ["b" * 2001]
        with self.assertRaises(ValueError): canonicalize_payload(over, max_aggregated_string_bytes=512000)
    def test_context_redacts_path_and_freezes_nested_metadata(self):
        ctx = AnalysisContext(b"abc", "/home/private/user/page.html", capture_metadata={"nested": {"items": [1, 2]}})
        self.assertEqual(ctx.source_name, "page.html")
        with self.assertRaises(TypeError): ctx.capture_metadata["nested"]["x"] = 1
        with self.assertRaises(AttributeError): ctx.capture_metadata["nested"]["items"].append(3)
if __name__ == "__main__": unittest.main()
