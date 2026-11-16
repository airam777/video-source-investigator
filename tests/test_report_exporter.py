import json
import tempfile
import unittest
from pathlib import Path

from report_exporter import export_report, render_markdown, sanitize_value


class ReportExporterTests(unittest.TestCase):
    def setUp(self):
        self.report = {
            "title": "Example report",
            "source_provenance": {"raw_html_sha256": "a" * 64, "raw_html_bytes": 10},
            "parsed_observations": {
                "media": "https://cdn.example.test/private/movie.mp4?token=secret123&quality=1080",
                "track": "https://cdn.example.test/private/subs.vtt?signature=abc",
                "page": "https://example.test/watch?id=42&auth=private",
                "note": 'authorization="Bearer-secret"',
            },
        }

    def test_sanitizer_hides_media_paths_and_secrets_without_mutation(self):
        safe = sanitize_value(self.report)
        rendered = json.dumps(safe)
        self.assertNotIn("secret123", rendered)
        self.assertNotIn("Bearer-secret", rendered)
        self.assertNotIn("/private/movie.mp4", rendered)
        self.assertNotIn("/private/subs.vtt", rendered)
        self.assertNotIn("quality=1080", rendered)
        self.assertIn("id=42", rendered)
        self.assertEqual(self.report["parsed_observations"]["media"].split("?")[1],
                         "token=secret123&quality=1080")

    def test_json_and_markdown_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "report.json"
            md_path = Path(tmp) / "report.md"
            export_report(self.report, json_path, md_path)
            parsed = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = md_path.read_text(encoding="utf-8")
            self.assertEqual(parsed["title"], "Example report")
            self.assertIn("# Exportovaný technický report", markdown)
            self.assertIn("Kontrola exportu", markdown)
            self.assertNotIn("secret123", json_path.read_text(encoding="utf-8"))
            self.assertNotIn("Bearer-secret", markdown)

    def test_markdown_renderer_sanitizes_even_when_called_directly(self):
        markdown = render_markdown(self.report)
        self.assertNotIn("secret123", markdown)
        self.assertNotIn("private/movie.mp4", markdown)


if __name__ == "__main__":
    unittest.main()
