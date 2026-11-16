import unittest
from core.sanitization import _validate_percent_encoding, validate_url
class SanitizationTests(unittest.TestCase):
    def test_accepts_http_https_and_ipv6(self):
        self.assertEqual(validate_url("https://example.test/path"), "https://example.test/path")
        self.assertEqual(validate_url("http://[2001:db8::1]/x"), "http://[2001:db8::1]/x")
    def test_rejects_userinfo_bad_scheme_and_bad_port(self):
        for url in ("javascript:alert(1)", "https://user:pass@example.test/", "https://example.test:99999/"):
            with self.subTest(url=url), self.assertRaises(ValueError): validate_url(url)
    def test_rejects_ambiguous_numeric_hosts(self):
        for host in ("0177.0.0.1", "0x7f000001", "2130706433"):
            with self.subTest(host=host), self.assertRaises(ValueError): validate_url("http://" + host + "/")
    def test_rejects_malformed_and_nested_traversal(self):
        for path in ("/%ZZ", "/%2e%2e/private", "/%252e%252e/private", "/%25252e%25252e/private"):
            with self.subTest(path=path), self.assertRaises(ValueError): _validate_percent_encoding(path)
    def test_rejects_incomplete_percent_escape(self):
        with self.assertRaises(ValueError): _validate_percent_encoding("/abc%2")
if __name__ == "__main__": unittest.main()
