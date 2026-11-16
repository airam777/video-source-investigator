import json
import unittest
from pathlib import Path


REPORT = (
    Path(__file__).resolve().parents[1]
    / "reports"
    / "ali-g-gdo-bit-ja-2026-reported-extraction.json"
)


class ReportProvenanceTests(unittest.TestCase):
    def test_report_is_valid_json_and_labels_unverified_source(self):
        data = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(
            data["evidence_status"],
            "user_supplied_extraction_not_independently_verified",
        )
        self.assertFalse(data["source_provenance"]["raw_html_available"])
        self.assertIsNone(data["source_provenance"]["raw_html_sha256"])
        self.assertFalse(data["source_provenance"]["parser_executed_on_original_html"])

    def test_report_contains_expected_structured_metadata(self):
        data = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(data["video"]["video_id"], "30639124")
        self.assertEqual(data["video"]["duration_seconds"], 5486)
        self.assertEqual(data["player"]["reported_active_player"], "videojs")
        self.assertEqual(len(data["cdn_hosts"]), 3)
        self.assertEqual(len(data["subtitles"]), 2)

    def test_report_does_not_claim_to_contain_signed_media_urls(self):
        rendered = REPORT.read_text(encoding="utf-8")
        self.assertNotIn("signature=", rendered)
        self.assertNotIn("token=", rendered)
        self.assertNotIn("cookies", rendered.lower().replace("no signed media urls, token values, cookies, or authorization material are stored in this report.", ""))


if __name__ == "__main__":
    unittest.main()
