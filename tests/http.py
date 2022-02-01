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

        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 11.3; rv:88.0) Gecko/20100101 Firefox/88.0"

        for original_url, canonical_url in [
            (
                "https://nbcnews.to/2Yc5JVz",
                "https://www.nbcnews.com/politics/congress/senate-vote-9-11-first-responders-bill-tuesday-n1032831?cid=sm_npd_nn_tw_ma",
            ),
            (
                "https://www.google.com/maps/d/viewer?mid=zQ8Zk-5ey-Y8.kgD9Rxu8JCNQ&hl=en&usp=sharing",
                "https://www.google.com/maps/d/viewer?mid=1NQVHeBBcVAnz9JwX1frZxX1ZgjY",
            ),
            (
                "https://pewrsr.ch/2kk3VvY",
                "https://www.pewresearch.org/internet/2019/09/05/more-than-half-of-u-s-adults-trust-law-enforcement-to-use-facial-recognition-responsibly/",
            ),
            (
                "https://pewrsr.ch/2ly4LFE",
                "https://www.pewresearch.org/internet/2019/09/05/the-challenges-of-using-machine-learning-to-identify-gender-in-images/",
            ),
            (
                "https://pewrsr.ch/2lxB0EX",
                "https://www.pewresearch.org/interactives/how-does-a-computer-see-gender/",
            ),
        ]:
            result = canonical_link(original_url, user_agent=user_agent, timeout=60)
            self.assertEqual(result, canonical_url)

    def test_trim_get_parameters(self):
        from pewtils.http import trim_get_parameters

        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 11.3; rv:88.0) Gecko/20100101 Firefox/88.0"
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
            GENERAL_LINK_SHORTENERS,
            VANITY_LINK_SHORTENERS,
            HISTORICAL_VANITY_LINK_SHORTENERS,
            trim_get_parameters,
        )

        # These are domains that resolve properly but are alternatives to a preferred version
        IGNORE_DOMAINS = [
            "ap.org",
            "cnet.co",
            "de.gov",
            "huffpost.com",
            "ky.gov",
            "mt.gov",
            "sen.gov",
            "twimg.com",
        ]

        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 11.3; rv:88.0) Gecko/20100101 Firefox/88.0"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        for k, v in VANITY_LINK_SHORTENERS.items():
            if (
                k not in HISTORICAL_VANITY_LINK_SHORTENERS.keys()
                and k not in IGNORE_DOMAINS
            ):
                try:
                    resp = self.session.head("http://{}".format(k), allow_redirects=True, timeout=10)

                except requests.exceptions.ConnectionError:
                    print(f"Could not resolve short domain (may be historic): {k} (connection error)")
                    resp = None

                if resp:
                    resp_url = trim_get_parameters(resp.url, session=self.session, timeout=10).split("?")[0]

                    if k in resp_url:
                        print(f"Short domain resolved but full domain unexpected (may be historic): {k} (resolved to {resp_url} but expected {v})")

                    else:
                        resolved = re.match(
                            "(www[0-9]?\.)?([^:]+)(:\d+$)?",
                            urlparse.urlparse(resp.url).netloc,
                        ).group(2)
                        resolved = VANITY_LINK_SHORTENERS.get(resolved, resolved)
                        # Vanity domains are often purchased/managed through bit.ly or trib.al, and don't resolve
                        # to their actual website unless paired with an actual page URL; so as long as they resolve
                        # to what we expect, or a generic vanity URL like bit.ly, we'll assume everything's good
                        self.assertTrue(resolved in GENERAL_LINK_SHORTENERS or v in resolved)

        self.session.close()

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
        if getattr(self, 'session', None) is not None:
            self.session.close()
