import tempfile
import unittest
from pathlib import Path

from deferred_player_inspector import inspect_html


class DeferredPlayerTests(unittest.TestCase):
    def test_reports_declared_ajax_shape_without_requesting_it(self):
        html = '''<html><body><div id="player"></div><script>
        $.ajax({url: "/players/load?token=secret", method: "POST", data: {id: "abc", type: "movie"}});
        $("#player");
        </script></body></html>'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            path.write_text(html, encoding="utf-8")
            report = inspect_html(path)
        self.assertTrue(report["player_loader_present"])
        self.assertFalse(report["jquery_ajax_declarations"][0]["request_performed_by_this_tool"])
        self.assertEqual(report["jquery_ajax_declarations"][0]["endpoint_declared_in_source"], "/players/load")
        self.assertIn("player", report["page_element_ids"])
        self.assertEqual(report["jquery_ajax_declarations"][0]["parameter_values"]["id"], "[redacted]")
        self.assertNotIn("secret", str(report))


if __name__ == "__main__":
    unittest.main()
