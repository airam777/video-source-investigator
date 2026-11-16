import unittest

from provenance_inspector import inspect_html


class ProvenanceInspectorTests(unittest.TestCase):
    def test_detects_explicit_uploader_profile_link(self):
        html = """
        <div>Uploaded by <a href="/user/filmfan?session=secret">FilmFan</a></div>
        """
        report = inspect_html(html, "https://prehraj.to/video/abc")
        self.assertTrue(report["uploader_identified"])
        uploader = next(x for x in report["explicit_attributions"] if x["kind"] == "uploader")
        self.assertEqual(uploader["name"], "FilmFan")
        self.assertEqual(uploader["public_profile_or_author_url"], "https://prehraj.to/user/filmfan")
        self.assertNotIn("secret", str(report))

    def test_distinguishes_page_author_from_uploader(self):
        html = '<meta name="author" content="Editorial Team">'
        report = inspect_html(html)
        self.assertFalse(report["uploader_identified"])
        self.assertEqual(report["explicit_attributions"][0]["kind"], "page_author")

    def test_reads_jsonld_uploader_without_claiming_license(self):
        html = '''
        <script type="application/ld+json">
        {"@type":"VideoObject","uploader":{"@type":"Person","name":"Uploader42","url":"https://example.test/@uploader42"}}
        </script>
        '''
        report = inspect_html(html)
        self.assertTrue(report["uploader_identified"])
        self.assertIn("does not prove ownership or licensing", report["note"])


if __name__ == "__main__":
    unittest.main()
