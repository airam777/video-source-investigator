import json
import unittest
from pathlib import Path


REPORT = (
    Path(__file__).resolve().parents[1]
    / "reports"
    / "ali-g-gdo-bit-ja-2026-reported-extraction.json"
)


class ReportProvenanceTests(unittest.TestCase):
    def test_report_is_valid_json_and_labels_source_hash(self):
        data = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(
            data["evidence_status"],
            "user_supplied_html_source_parsed_offline_in_conversation",
        )
        provenance = data["source_provenance"]
        self.assertTrue(provenance["raw_html_available_in_conversation"])
        self.assertEqual(len(provenance["raw_html_sha256"]), 64)
        self.assertEqual(provenance["raw_html_bytes"], 4283)
        self.assertTrue(provenance["parser_executed_on_supplied_html"])

    def test_report_contains_expected_observations(self):
        data = json.loads(REPORT.read_text(encoding="utf-8"))
        parsed = data["parsed_observations"]
        self.assertEqual(parsed["video_id"], 30639124)
        self.assertEqual(parsed["duration_seconds"], 5486)
        self.assertEqual(parsed["player"], "videojs")
        self.assertEqual(len(parsed["cdn_hosts"]), 3)
        self.assertEqual(len(parsed["subtitle_ids"]), 2)

    def test_report_excludes_signed_url_material(self):
        rendered = REPORT.read_text(encoding="utf-8")
        self.assertNotIn("signature=", rendered)
        self.assertNotIn("expires=", rendered)
        self.assertNotIn("token=", rendered)


if __name__ == "__main__":
    unittest.main()
