from __future__ import print_function
import unittest


class HTTPTests(unittest.TestCase):
    """
    To test, navigate to pewtils root folder and run `python -m unittest tests`
    """

    def setUp(self):
        pass

    def test_hash_url(self):
        from pewtils.http import hash_url
        url = hash_url("http://www.example.com")
        self.assertTrue(url == "7c1767b30512b6003fd3c2e618a86522")
        url = hash_url("www.example.com")
        self.assertTrue(url == "7c1767b30512b6003fd3c2e618a86522")

    def test_new_random_number(self):
        from pewtils.http import new_random_number
        import numpy as np
        maxes = [1, 2, 4, 8, 10]
        avgs = [1, 1, 2, 4, 6]
        for attempt, attempt_max, attempt_avg in zip(range(5), maxes, avgs):
            attempts = [new_random_number(attempt=attempt) for i in range(500)]
            self.assertTrue(round(np.average(attempts)) <= attempt_avg)
            self.assertTrue(max(attempts) < attempt_max)

    def test_strip_html(self):
        # example.html taken from example.com on 3/5/19
        from contextlib import closing
        with closing(open("tests/files/example.html", "r")) as input:
            html = input.read()
        from pewtils.http import strip_html
        stripped_html = strip_html(html, simple=False)
        stripped_simple_html = strip_html(html, simple=True)
        # with closing(open("tests/files/example_stripped.html", "w")) as output:
        #     output.write(stripped_html)
        # with closing(open("tests/files/example_stripped_simple.html", "w")) as output:
        #     output.write(stripped_simple_html)

        with closing(open("tests/files/example_stripped.html", "r")) as input:
            text = input.read()
            self.assertTrue(text == stripped_html)
        with closing(open("tests/files/example_stripped_simple.html", "r")) as input:
            text = input.read()
            self.assertTrue(text == stripped_simple_html)

    def tearDown(self):
        pass