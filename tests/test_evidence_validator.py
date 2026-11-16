import unittest

from evidence_validator import evidence_category, safe_host_reference, validate_report


class EvidenceValidatorTests(unittest.TestCase):
    def test_schema_categories(self):
        self.assertEqual(evidence_category("video_id"), "direct_html")
        self.assertEqual(evidence_category("cdn_storage_hosts"), "direct_html")
        self.assertEqual(evidence_category("transcoding_interpretation"), "derived_or_transcoded")
        self.assertEqual(evidence_category("original_file_size_bytes"), "reported_external")
        self.assertEqual(evidence_category("url_tokens_present"), "security_and_actions")
        self.assertEqual(evidence_category("invented_field"), "unclassified")

    def test_validates_provenance_and_keeps_caveats(self):
        report = {
            "source_provenance": {
                "raw_html_sha256": "a" * 64,
                "raw_html_bytes": 4283,
                "raw_html_available_in_conversation": True,
                "project_parser_executed": False,
            },
            "parsed_observations": {
                "cdn_hosts": ["cdn.example.test"],
                "uploader_label": "Example uploader template",
                "streaming_variants_mp4": ["1080p", "720p"],
            },
        }
        result = validate_report(report)
        self.assertTrue(result["valid"])
        self.assertTrue(any("project parser" in x for x in result["warnings"]))
        self.assertTrue(any("natural person" in x for x in result["warnings"]))
        self.assertTrue(any("transcoding history" in x for x in result["warnings"]))

    def test_rejects_invalid_hash_and_signed_url(self):
        report = {
            "source_provenance": {"raw_html_sha256": "not-a-hash"},
            "notes": ["https://cdn.example.test/file.mp4?token=DO_NOT_STORE"],
        }
        result = validate_report(report)
        self.assertFalse(result["valid"])
        self.assertTrue(any("SHA-256" in x for x in result["errors"]))
        self.assertTrue(any("sensitive query" in x for x in result["errors"]))

    def test_safe_host_reference_discards_path_and_query(self):
        value = safe_host_reference("https://cdn.example.test/private/file.mp4?token=secret")
        self.assertEqual(value, "https://cdn.example.test/[reference hidden]")
        self.assertNotIn("secret", value)
        self.assertNotIn("file.mp4", value)


if __name__ == "__main__":
    unittest.main()
