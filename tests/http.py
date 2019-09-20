from __future__ import print_function
import unittest, re


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

    def test_canonical_link(self):

        from pewtils.http import canonical_link
        user_agent = "Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)'"

        # TODO: continue testing canonical_link
        # canonical_link("https://t.co/H9tE3IlTAH")
        # canonical_link("http://ow.ly/M5o4N")
        # canonical_link("https://bit.ly/2CTCEFW")
        # canonical_link("https://nbcnews.to/2Yc5JVz")
        # canonical_link("https://www.c-span.org/Live-Video/C-SPAN")
        # canonical_link("http://bit.ly/ascWO6")
        # canonical_link("https://www.google.com/maps/d/viewer?mid=zQ8Zk-5ey-Y8.kgD9Rxu8JCNQ&hl=en&usp=sharing")
        # canonical_link("https://goo.gl/images/WS5JSd")
        for original_url, canonical_url in [
            ("https://httpbin.org/redirect/10", "https://httpbin.org/relative-redirect/1"),
            ("https://httpbin.org/redirect-to?url=status%2F200", ""),
            ("https://httpbin.org/redirect-to?url=status%2F301", ""),
            ("https://httpbin.org/redirect-to?url=status%2F302", ""),
            ("https://httpbin.org/redirect-to?url=status%2F303", "https://httpbin.org/status/303"),
            ("https://httpbin.org/redirect-to?url=status%2F307", "https://httpbin.org/status/307"),
            ("https://httpbin.org/redirect-to?url=status%2F308", "https://httpbin.org/status/308"),
            ("https://httpbin.org/redirect-to?url=status%2F400", ""),
            ("https://httpbin.org/redirect-to?url=status%2F401", "https://httpbin.org/status/401"),
            ("https://httpbin.org/redirect-to?url=status%2F403", "https://httpbin.org/status/403"),
            ("https://httpbin.org/redirect-to?url=status%2F404", ""),
            ("https://httpbin.org/redirect-to?url=status%2F500", ""),
            ("https://httpbin.org/relative-redirect/10", ""),
            ("https://pewrsr.ch/2kk3VvY", "https://www.pewinternet.org/2019/09/05/more-than-half-of-u-s-adults-trust-law-enforcement-to-use-facial-recognition-responsibly/"),
            ("https://pewrsr.ch/2ly4LFE", "https://www.pewinternet.org/essay/the-challenges-of-using-machine-learning-to-identify-gender-in-images/"),
            ("https://pewrsr.ch/2lxB0EX", "https://www.pewresearch.org/interactives/how-does-a-computer-see-gender/")
        ]:
            result = canonical_link(original_url, user_agent=user_agent, timeout=30)
            # print(result)
            # import pdb; pdb.set_trace()

    def test_link_shortener_map(self):

        import requests
        from six.moves.urllib import parse as urlparse
        from pewtils.http import VANITY_LINK_SHORTENERS
        user_agent = "Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)'"
        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})
        for k, v in VANITY_LINK_SHORTENERS.items():
            resp = session.head("http://{}".format(k), allow_redirects=True, timeout=10)
            resolved = re.sub("www\.", "", urlparse.urlparse(resp.url).netloc)
            resolved = VANITY_LINK_SHORTENERS.get(resolved, resolved)
            print("{} -> {}".format(k, resolved))
            self.assertIn(resolved, ["bitly.com", v])
        session.close()


    def test_extract_domain_from_url(self):

        pass


    def tearDown(self):
        pass