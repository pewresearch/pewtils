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
        self.assertEqual(url, "7c1767b30512b6003fd3c2e618a86522")
        url = hash_url("www.example.com")
        self.assertEqual(url, "7c1767b30512b6003fd3c2e618a86522")

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
            self.assertEqual(text, stripped_html)
        with closing(open("tests/files/example_stripped_simple.html", "r")) as input:
            text = input.read()
            self.assertEqual(text, stripped_simple_html)

    def test_canonical_link(self):

        from pewtils.http import canonical_link

        user_agent = "Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)'"

        for original_url, canonical_url in [
            (
                "t.co/H9tE3IlTAH",
                "https://www.cnn.com/2018/04/01/politics/trump-no-more-daca-deal/index.html?sr=twCNN040118trump-no-more-daca-deal1059AMVODtop",
            ),
            (
                "https://t.co/H9tE3IlTAH",
                "https://www.cnn.com/2018/04/01/politics/trump-no-more-daca-deal/index.html?sr=twCNN040118trump-no-more-daca-deal1059AMVODtop",
            ),
            (
                "http://ow.ly/M5o4N",
                "https://snjtoday.com/congressman-fran56754k-lobiondo-visits-vineland-high-school/",
            ),
            (
                "https://bit.ly/2CTCEFW",
                "https://action.tinaforminnesota.com/page/s/tsm_20190130_backpay",
            ),
            (
                "https://nbcnews.to/2Yc5JVz",
                "https://www.nbcnews.com/politics/congress/senate-vote-9-11-first-responders-bill-tuesday-n1032831?cid=sm_npd_nn_tw_ma",
            ),
            (
                "https://www.c-span.org/Live-Video/C-SPAN",
                "https://www.c-span.org/Live-Video/C-SPAN",
            ),
            ("http://bit.ly/ascWO6", "http://irtl.org/html/DanCoats.mp3"),
            (
                "https://www.google.com/maps/d/viewer?mid=zQ8Zk-5ey-Y8.kgD9Rxu8JCNQ&hl=en&usp=sharing",
                "https://www.google.com/maps/d/viewer?mid=1NQVHeBBcVAnz9JwX1frZxX1ZgjY",
            ),
            (
                "https://goo.gl/images/WS5JSd",
                "https://www.healthcare.gov/blog/sign-up-by-december-15/",
            ),
            (
                "https://httpbin.org/redirect/10",
                "https://httpbin.org/relative-redirect/1",
            ),
            (
                "https://httpbin.org/redirect-to?url=status%2F303",
                "https://httpbin.org/status/303",
            ),
            (
                "https://httpbin.org/redirect-to?url=status%2F307",
                "https://httpbin.org/status/307",
            ),
            (
                "https://httpbin.org/redirect-to?url=status%2F308",
                "https://httpbin.org/status/308",
            ),
            (
                "https://httpbin.org/redirect-to?url=status%2F401",
                "https://httpbin.org/status/401",
            ),
            (
                "https://httpbin.org/redirect-to?url=status%2F403",
                "https://httpbin.org/status/403",
            ),
            (
                "https://pewrsr.ch/2kk3VvY",
                "https://www.pewinternet.org/2019/09/05/more-than-half-of-u-s-adults-trust-law-enforcement-to-use-facial-recognition-responsibly/",
            ),
            (
                "https://pewrsr.ch/2ly4LFE",
                "https://www.pewinternet.org/essay/the-challenges-of-using-machine-learning-to-identify-gender-in-images/",
            ),
            (
                "https://pewrsr.ch/2lxB0EX",
                "https://www.pewresearch.org/interactives/how-does-a-computer-see-gender/",
            ),
        ]:
            result = canonical_link(original_url, user_agent=user_agent, timeout=30)

    def test_trim_get_parameters(self):
        from pewtils.http import trim_get_parameters

        user_agent = "Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)'"
        for original_url, trimmed_url in [
            ("https://httpbin.org/status/200", "https://httpbin.org/status/200"),
            (
                "https://httpbin.org/status/200?param=1",
                "https://httpbin.org/status/200",
            ),
        ]:
            trimmed = trim_get_parameters(
                original_url, user_agent=user_agent, timeout=30
            )
            self.assertEqual(trimmed, trimmed_url)

    def test_link_shortener_map(self):

        import requests
        from six.moves.urllib import parse as urlparse
        from pewtils.http import (
            VANITY_LINK_SHORTENERS,
            HISTORICAL_VANITY_LINK_SHORTENERS,
        )

        user_agent = "Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)'"
        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})
        for k, v in VANITY_LINK_SHORTENERS.items():
            if k not in HISTORICAL_VANITY_LINK_SHORTENERS.keys():
                resp = session.head(
                    "http://{}".format(k), allow_redirects=True, timeout=10
                )
                resolved = re.sub("www\.", "", urlparse.urlparse(resp.url).netloc)
                resolved = VANITY_LINK_SHORTENERS.get(resolved, resolved)
                self.assertIn(resolved, ["bitly.com", v])
        session.close()

    def test_extract_domain_from_url(self):
        from pewtils.http import extract_domain_from_url

        for url, domain, include_subdomain, resolve in [
            ("https://pewrsr.ch/2lxB0EX", "pewresearch.org", False, False),
            ("https://pewrsr.ch/2lxB0EX", "pewresearch.org", False, True),
            ("https://nbcnews.to/2Yc5JVz", "nbcnews.com", False, False),
            ("https://nbcnews.to/2Yc5JVz", "nbcnews.com", False, True),
            ("https://news.ycombinator.com", "ycombinator.com", False, False),
            ("https://news.ycombinator.com", "news.ycombinator.com", True, False),
            ("http://forums.bbc.co.uk", "forums.bbc.co.uk", True, False),
            ("http://forums.bbc.co.uk", "bbc.co.uk", False, False),
            ("http://www.worldbank.org.kg/", "worldbank.org.kg", True, False),
            ("http://forums.news.cnn.com/", "forums.news.cnn.com", True, False),
            ("http://forums.news.cnn.com/", "cnn.com", False, False),
        ]:
            extracted_domain = extract_domain_from_url(
                url, include_subdomain=include_subdomain, resolve_url=resolve
            )
            self.assertEqual(extracted_domain, domain)

    def tearDown(self):
        pass
