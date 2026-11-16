import json
import tempfile
import unittest
from pathlib import Path

from analyze_page import analyze
from authorized_stream_extractor import extract
from deferred_player_inspector import inspect_html as inspect_deferred
from investigator import inspect_html
from provenance_inspector import inspect_html as inspect_provenance
from provider_inspector import inspect as inspect_provider


SAMPLE = """<!doctype html>
<html><head>
<title>Sample video page</title>
<link rel="canonical" href="https://example.test/item/123">
<meta property="og:title" content="Sample video page">
<meta property="og:video" content="https://cdn.example.test/path/video.mp4?token=SECRET&expires=123">
<meta name="author" content="Editorial team">
</head><body>
<iframe src="https://embed.example.test/player/123"></iframe>
<video data-setup='{"controls": true}'><source src="https://cdn.example.test/movie.mp4?signature=SECRET" type="video/mp4"></video>
<script>
var player = "videojs";
$.ajax({url: "/ajax/videoStarted", method: "POST", data: {videoId: "123", token: "SECRET"}});
</script>
</body></html>"""


class OfflineAnalyzerTests(unittest.TestCase):
    def test_general_inspector_redacts_signed_media_reference(self):
        report = inspect_html(SAMPLE, base_url="https://example.test/item/123")
        rendered = json.dumps(report)
        self.assertIn("cdn.example.test", rendered)
        self.assertNotIn("SECRET", rendered)
        self.assertNotIn("video.mp4", rendered)
        self.assertEqual(report["title"], "Sample video page")

    def test_provider_inspector_detects_videojs_and_hosts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.html"
            path.write_text(SAMPLE, encoding="utf-8")
            report = inspect_provider(path, "https://example.test/item/123")
        self.assertTrue(any(x["player"] == "Video.js" for x in report["player_configurations"]))
        self.assertTrue(any("cdn.example.test" in x["host"] for x in report["provider_hosts"]))

    def test_media_extractor_reports_host_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.html"
            path.write_text(SAMPLE, encoding="utf-8")
            report = extract(path, "https://example.test/item/123")
        rendered = json.dumps(report)
        self.assertIn("cdn.example.test", rendered)
        self.assertNotIn("SECRET", rendered)
        self.assertNotIn("movie.mp4", rendered)
        self.assertFalse(report["full_urls_shown"])

    def test_deferred_loader_is_described_not_called(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.html"
            path.write_text(SAMPLE, encoding="utf-8")
            report = inspect_deferred(path)
        self.assertEqual(report["jquery_ajax_declarations"][0]["method"], "POST")
        self.assertIn("videoId", report["jquery_ajax_declarations"][0]["parameter_names"])
        self.assertFalse(report["jquery_ajax_declarations"][0]["request_performed_by_this_tool"])
        self.assertNotIn("SECRET", json.dumps(report))

    def test_attribution_does_not_promote_author_to_uploader(self):
        report = inspect_provenance(SAMPLE, "https://example.test/item/123")
        self.assertFalse(report["uploader_identified"])
        self.assertEqual(report["explicit_attributions"][0]["kind"], "page_author")

    def test_consolidated_report_is_offline_and_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.html"
            path.write_text(SAMPLE, encoding="utf-8")
            report = analyze(path, "https://example.test/item/123")
        rendered = json.dumps(report)
        self.assertEqual(report["title"], "Sample video page")
        self.assertNotIn("SECRET", rendered)
        self.assertTrue(any("no remote requests" in x.lower() for x in report["interpretation"]))


if __name__ == "__main__":
    unittest.main()
