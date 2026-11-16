import tempfile
import unittest
from pathlib import Path

from provider_inspector import inspect


class ProviderInspectorTests(unittest.TestCase):
    def test_detects_player_configs_and_media_types_without_urls(self):
        html = """
        <html><head><title>Authorized demo</title></head><body>
        <video><source src="https://cdn.example.test/demo.mp4?token=secret" type="video/mp4"></video>
        <script>
          jwplayer("player").setup({file: "https://media.example.test/master.m3u8?sig=secret"});
          videojs("my-player", {sources: [{src: "https://cdn.example.test/clip.mp4", type: "video/mp4"}]});
        </script>
        </body></html>
        """
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "page.html"
            path.write_text(html, encoding="utf-8")
            report = inspect(path)

        players = {x["player"] for x in report["player_configurations"]}
        self.assertIn("JW Player", players)
        self.assertIn("Video.js", players)
        kinds = {x["media_type"] for x in report["references"]}
        self.assertIn("MP4", kinds)
        self.assertIn("HLS playlist", kinds)
        rendered = str(report)
        self.assertNotIn("secret", rendered)
        self.assertNotIn("demo.mp4", rendered)
        self.assertNotIn("master.m3u8", rendered)


if __name__ == "__main__":
    unittest.main()
