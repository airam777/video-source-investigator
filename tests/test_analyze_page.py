import tempfile
import unittest
from pathlib import Path

from analyze_page import analyze


class CombinedReportTests(unittest.TestCase):
    def test_combines_provider_loader_media_and_attribution_without_playable_url(self):
        html = """
        <html><head><title>Authorized sample</title></head><body>
          <div>Uploaded by <a href="/user/demo?session=private">DemoUploader</a></div>
          <iframe data-src="https://voe.sx/e/example"></iframe>
          <video><source src="https://cdn.example.test/sample.mp4?token=secret" type="video/mp4"></video>
          <script>
            jwplayer("player").setup({file: "https://cdn.example.test/master.m3u8?sig=secret"});
            $.ajax({url: "/player/load", method: "POST", data: {id: "demo"}});
          </script>
        </body></html>
        """
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "page.html"
            path.write_text(html, encoding="utf-8")
            report = analyze(path, "https://catalog.example.test/watch/1")

        self.assertEqual(report["title"], "Authorized sample")
        self.assertIn("voe.sx", report["provider_hosts"])
        self.assertTrue(report["deferred_loader"]["player_loader_present"])
        self.assertTrue(report["uploader_identified"])
        self.assertEqual(report["explicit_attributions"][0]["name"], "DemoUploader")
        rendered = str(report)
        self.assertNotIn("private", rendered)
        self.assertNotIn("secret", rendered)
        self.assertNotIn("sample.mp4", rendered)
        self.assertNotIn("master.m3u8", rendered)
        self.assertTrue(report["source_provenance"]["project_parser_executed"])
        self.assertEqual(report["source_provenance"]["raw_html_bytes"], len(html.encode("utf-8")))
        self.assertTrue(report["evidence_validation"]["valid"])

    def test_cli_exports_redacted_json_and_markdown(self):
        import json
        import subprocess
        import sys

        html = '<html><head><title>CLI sample</title></head><body><video src="https://cdn.example.test/file.mp4?token=secret"></video></body></html>'
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "input.html"
            json_path = root / "report.json"
            markdown_path = root / "report.md"
            source.write_text(html, encoding="utf-8")
            subprocess.run(
                [sys.executable, "analyze_page.py", str(source), "--json", str(json_path), "--markdown", str(markdown_path)],
                check=True, capture_output=True, text=True,
            )
            json_text = json_path.read_text(encoding="utf-8")
            markdown_text = markdown_path.read_text(encoding="utf-8")
            exported = json.loads(json_text)
            self.assertEqual(exported["title"], "CLI sample")
            self.assertIn("source_provenance", exported)
            self.assertIn("evidence_validation", exported)
            self.assertIn("Declared Media Evidence", markdown_text)
            self.assertNotIn("secret", json_text)
            self.assertNotIn("file.mp4", markdown_text)


if __name__ == "__main__":
    unittest.main()
