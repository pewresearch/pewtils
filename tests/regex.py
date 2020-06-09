import unittest


class RegexTests(unittest.TestCase):

    """
    To test, navigate to pewtils root folder and run `python -m unittest tests`
    """

    def setUp(self):
        pass

    def test_url_regex(self):

        from pewtils.regex import URL_REGEX

        for val in [
            "example.com",
            "www.example.com",
            "http://example.com",
            "https://example.com",
            "https://www.example.com",
            "example.com/test",
            "example.com/test?test=test",
            "http://example.com?test=test&test=test",
            "https://t.co/example",
        ]:
            result = URL_REGEX.findall("test {} test".format(val))
            self.assertEqual(result[0], val)

    def test_domain_regex(self):
        from pewtils.regex import DOMAIN_REGEX

        for val in ["example.com", "http://example.com"]:
            result = DOMAIN_REGEX.findall(val)
            self.assertEqual(result[0], "example.com")
        for val in [
            "test.example.com",
            "http://test.example.com",
            "https://www.test.example.com",
            "test.example.com/test",
        ]:
            result = DOMAIN_REGEX.findall(val)
            self.assertEqual(result[0], "test.example.com")

    def test_http_regex(self):

        from pewtils.regex import HTTP_REGEX

        for val in [
            "http://example.com",
            "https://example.com",
            "https://www.example.com",
            "http://example.com?test=test&test=test",
        ]:
            result = HTTP_REGEX.match(val)
            self.assertIsNotNone(result)

        for val in [
            "example.com",
            "www.example.com",
            "example.com/test",
            "example.com/test?test=test",
        ]:
            result = HTTP_REGEX.match(val)
            self.assertIsNone(result)

    def test_us_dollar_regex(self):
        from pewtils.regex import US_DOLLAR_REGEX

        for val in [
            "$1.00",
            "$10",
            "$10,000",
            "$999,999",
            "$1,000,000,000",
            "$1,000,000,000.00",
        ]:
            result = US_DOLLAR_REGEX.findall(val)
            self.assertEqual(result[0], val)

        for val in ["$01,000", "$01", "$1a0,000", "$.00", "$01.00"]:
            result = US_DOLLAR_REGEX.findall(val)
            self.assertEqual(len(result), 0)

    def test_titleword_regex(self):
        from pewtils.regex import TITLEWORD_REGEX

        for val, expected in [
            ("this is a Test", ["Test"]),
            ("testing One two three", ["One"]),
            ("testing One Two Three", ["One", "Two", "Three"]),
            ("testing One1 Two2 Three3", []),
            ("testing one two three", []),
        ]:
            result = TITLEWORD_REGEX.findall(val)
            self.assertEqual(result, expected)

    def test_number_regex(self):
        from pewtils.regex import NUMBER_REGEX

        for val, expected in [
            ("one 2 three", ["2"]),
            ("1234", ["1234"]),
            (" 12 345 ", ["12", "345"]),
            ("one2three", []),
        ]:
            result = NUMBER_REGEX.findall(val)
            self.assertEqual(result, expected)

    def test_nonalpha_regex(self):
        from pewtils.regex import NONALPHA_REGEX

        for val, expected in [
            ("abc$efg", ["$"]),
            ("one ^%& two", [" ", "^", "%", "&", " "]),
            ("one two three", [" ", " "]),
            ("1234", []),
        ]:
            result = NONALPHA_REGEX.findall(val)
            self.assertEqual(result, expected)
