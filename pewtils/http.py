from __future__ import division
from bs4 import BeautifulSoup
from builtins import str
from pewtils import get_hash, decode_text, is_not_null
from six.moves.urllib import parse as urlparse
from unidecode import unidecode
import pandas as pd
import re
import os
import requests
import tldextract
import warnings
from requests.exceptions import ReadTimeout
from stopit import ThreadingTimeout as Timeout


_ = pd.read_csv(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "general_link_shorteners.csv"
    )
)
GENERAL_LINK_SHORTENERS = _["shortener"].values


_ = pd.read_csv(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "vanity_link_shorteners.csv"
    )
)
_ = _[_["historical"] == 0]
VANITY_LINK_SHORTENERS = dict(zip(_["shortener"], _["expanded"]))

_ = pd.read_csv(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "vanity_link_shorteners.csv"
    )
)
_ = _[_["historical"] == 1]
HISTORICAL_VANITY_LINK_SHORTENERS = dict(zip(_["shortener"], _["expanded"]))

VANITY_LINK_SHORTENERS.update(HISTORICAL_VANITY_LINK_SHORTENERS)


def hash_url(url):

    """
    Clears out http/https prefix and returns an MD5 hash of the URL. More effective \
    when used in conjunction with :py:func:`pewtils.http.canonical_link`.

    :param url: The URL to hash
    :type url: str
    :return: Hashed string representation of the URL using the md5 hashing algorithm.
    :rtype: str

    Usage::

        from pewtils.http import hash_url

        >>> hash_url("http://www.example.com")
        "7c1767b30512b6003fd3c2e618a86522"
        >>> hash_url("www.example.com")
        "7c1767b30512b6003fd3c2e618a86522"

    """

    http_regex = re.compile(r"^http(s)?\:\/\/")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = get_hash(
            unidecode(http_regex.sub("", url.lower())), hash_function="md5"
        )
        return result


def strip_html(html, simple=False, break_tags=None):

    """
    Attempts to strip out HTML code from an arbitrary string while preserving meaningful text components. \
    By default, the function will use BeautifulSoup to parse the HTML. Setting ``simple=True`` will make the \
    function use a much simpler regular expression approach to parsing.

    :param html: The HTML to process
    :type html: str
    :param simple: Whether or not to use a simple regex or more complex parsing rules (default=False)
    :type simple: bool
    :param break_tags: A custom list of tags on which to break (default is ["strong", "em", "i", "b", "p"])
    :type break_tags: list
    :return: The text with HTML components removed
    :rtype: str

    .. note: This function might not be effective for *all* variations of HTML structures, but it produces fairly \
        reliable results in removing the vast majority of HTML without stripping out valuable content.

    Usage::

        from pewtils.http import strip_html

        >>> my_html = "<html><head>Header text</head><body>Body text</body></html>"
        >>> strip_html(my_html)
        'Header text Body text'

    """

    html = re.sub(r"\n", " ", html)
    html = re.sub(r"\s+", " ", html)
    if not break_tags:
        break_tags = ["strong", "em", "i", "b", "p"]
    if not simple:
        try:

            split_re = re.compile(r"\s{2,}")
            soup = BeautifulSoup(html, "lxml")
            for tag in soup():
                if (
                    "class" in tag.attrs
                    and ("menu" in tag.attrs["class"] or "header" in tag.attrs["class"])
                ) or ("menu" in str(tag.id) or "header" in str(tag.id)):
                    tag.extract()
            for tag in soup(["script", "style"]):
                tag.extract()
            for br in soup.find_all("br"):
                br.replace_with("\n")
            for t in soup(break_tags):
                try:
                    t.replace_with("\n{0}\n".format(t.text))
                except (UnicodeDecodeError, UnicodeEncodeError):
                    t.replace_with("\n{0}\n".format(decode_text(t.text)))
            if hasattr(soup, "body") and soup.body:
                text = soup.body.get_text()
            else:
                text = soup.get_text()
            lines = [l.strip() for l in text.splitlines()]
            lines = [l2.strip() for l in lines for l2 in split_re.split(l)]
            text = "\n".join([l for l in lines if l])
            text = re.sub(r"(\sA){2,}\s", " ", text)
            text = re.sub(r"\n+(\s+)?", "\n\n", text)
            text = re.sub(r" +", " ", text)
            text = re.sub(r"\t+", " ", text)

            return text

        except Exception as e:

            print("strip_html error")
            print(e)
            text = re.sub(r"<[^>]*>", " ", re.sub("\\s+", " ", html)).strip()
            return text

    else:
        return "\n".join(
            [
                re.sub(r"\s+", " ", re.sub(r"\<[^\>]+\>", " ", section))
                for section in re.sub(r"\<\/?div\>|\<\/?p\>|\<br\>", "\n", html).split(
                    "\n"
                )
            ]
        )


def trim_get_parameters(url, session=None, timeout=30, user_agent=None):

    """
    Takes a URL (presumed to be the final end point) and iterates over GET parameters, attempting to find optional
    ones that can be removed without generating any redirects.

    :param url: The URL to trim
    :type url: str
    :param session: (Optional) A persistent session that can optionally be passed (useful if you're processing many \
    links at once)
    :type session: :py:class:`requests.Session` object
    :param user_agent: User agent for the auto-created requests Session to use, if a preconfigured requests Session \
    is not provided
    :type user_agent: str
    :param timeout: Timeout for requests
    :type timeout: int or float
    :return: The original URL with optional GET parameters removed
    :rtype: str

    Usage::

        from pewtils.http import trim_get_parameters

        >>> trim_get_parameters("https://httpbin.org/status/200?param=1")
        "https://httpbin.org/status/200"

    """

    close_session = False
    if not session:
        close_session = True
        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})

    # Often there's extra information about social sharing and referral sources that can be removed
    ditch_params = []
    parsed = urlparse.urlparse(url)
    if parsed.query:
        params = urlparse.parse_qs(parsed.query)
        for k, v in params.items():
            # We iterate over all of the GET parameters and try holding each one out
            check = True
            for skipper in ["document", "article", "id", "qs"]:
                # If the parameter is named something that's probably a unique ID, we'll keep it
                if skipper in k.lower():
                    check = False
            for skipper in ["html", "http"]:
                # Same goes for parameters that contain URL information
                if skipper in v[0].lower():
                    check = False
            if check:
                new_params = {
                    k2: v2[0] for k2, v2 in params.items() if k2 != k and len(v2) == 1
                }
                new_params = urlparse.urlencode(new_params)
                new_parsed = parsed._replace(query=new_params)
                new_url = urlparse.urlunparse(new_parsed)
                try:
                    resp = session.head(new_url, allow_redirects=True, timeout=timeout)
                except ReadTimeout:
                    resp = None
                if is_not_null(resp):
                    new_parsed = urlparse.urlparse(resp.url)
                    if new_parsed.query != "" or new_parsed.path not in ["", "/"]:
                        # If removing a parameter didn't redirect to a root domain...
                        new_url = resp.url
                        compare_new = (
                            new_url.split("?")[0] if "?" in new_url else new_url
                        )
                        compare_old = url.split("?")[0] if "?" in url else url
                        if compare_new == compare_old:
                            # And the domain is the same as it was before, then the parameter was probably unnecessary
                            ditch_params.append(k)

    if len(ditch_params) > 0:
        # Now we remove all of the unnecessary get parameters and finalize the URL
        new_params = {
            k: v[0] for k, v in params.items() if len(v) == 1 and k not in ditch_params
        }
        new_params = urlparse.urlencode(new_params)
        parsed = parsed._replace(query=new_params)
        url = urlparse.urlunparse(parsed)

    if close_session:
        session.close()

    return url


def extract_domain_from_url(
    url,
    include_subdomain=True,
    resolve_url=False,
    timeout=1.0,
    session=None,
    user_agent=None,
    expand_shorteners=True,
):

    """
    Attempts to extract a standardized domain from a url by following the link and extracting the TLD.

    :param url:  The link from which to extract the domain
    :type url: str
    :param include_subdomain: Whether or not to include the subdomain (e.g. 'news.google.com'); default is True
    :type include_subdomain: bool
    :param resolve_url: Whether to fully resolve the URL.  If False (default), it will operate on the URL as-is; if \
    True, the URL will be passed to :py:func:`pewtils.http.canonical_link` to be standardized prior to extracting the \
    domain.
    :param timeout: (Optional, for use with ``resolve_url``) Maximum number of seconds to wait on a request before \
    timing out (default is 1)
    :type timeout: int or float
    :param session: (Optional, for use with ``resolve_url``) A persistent session that can optionally be passed \
    (useful if you're processing many links at once)
    :type session: :py:class:`requests.Session` object
    :param user_agent: (Optional, for use with ``resolve_url``) User agent for the auto-created requests Session to use, \
    if a preconfigured requests Session is not provided
    :type user_agent: str
    :param expand_shorteners: If True, shortened URLs that don't successfully expand will be checked against a list \
    of known URL shorteners and expanded if recognized. (Default = True)
    :type expand_shorteners: bool
    :return: The domain for the link
    :rtype: str

    .. note:: If ``resolve_url`` is set to True, the link will be standardized prior to domain extraction (in which \
        case you can provide optional timeout, session, and user_agent parameters that will be passed to \
        :py:func:`pewtils.http.canonical_link`). By default, however, the link will be operated on as-is. The final \
        extracted domain is then checked against known URL shorteners (see :ref:`vanity_link_shorteners`) and if it \
        is recognized, the expanded domain will be returned instead. Shortened URLs that are not standardized and \
        do not follow patterns included in this dictionary of known shorteners may be returned with an incorrect domain.

    Usage::

        from pewtils.http import extract_domain_from_url

        >>> extract_domain_from_url("http://forums.bbc.co.uk", include_subdomain=False)
        "bbc.co.uk"
        >>> extract_domain_from_url("http://forums.bbc.co.uk", include_subdomain=True)
        "forums.bbc.co.uk"

    """

    if resolve_url:
        url = canonical_link(
            url, timeout=timeout, session=session, user_agent=user_agent
        )
    domain = tldextract.extract(url)
    if domain:
        if include_subdomain and domain.subdomain and domain.subdomain != "www":
            domain = ".".join([domain.subdomain, domain.domain, domain.suffix])
        else:
            domain = ".".join([domain.domain, domain.suffix])
        if expand_shorteners:
            domain = VANITY_LINK_SHORTENERS.get(domain, domain)
    return domain


def canonical_link(url, timeout=5.0, session=None, user_agent=None):

    """
    Tries to resolve a link to the "most correct" version.

    Useful for expanding short URLs from bit.ly / Twitter and for checking HTTP status codes without retrieving \
    the actual data. Follows redirects and tries to pick the most informative version of a URL while avoiding \
    redirects to generic 404 pages. Also tries to iteratively remove optional GET parameters.

    May not be particularly effective on dead links, but may still be able to follow redirects enough \
    to return a URL with the correct domain associated with the original link.

    :param url: The URL to test. Should be fully qualified.
    :type url: str
    :param timeout: How long to wait for a response before giving up (default is one second)
    :type timeout: int or float
    :param session: (Optional) A persistent session that can optionally be passed (useful if you're processing many \
    links at once)
    :type session: :py:class:`requests.Session` object
    :param user_agent: User agent for the auto-created requests Session to use, if a preconfigured requests Session \
    is not provided
    :type user_agent: str
    :return: The "canonical" URL as supplied by the server, or the original URL if none supplied.
    :rtype: str

    .. note:: See :ref:`link_shorteners` for a complete list of shortened links recognized by this function.

        This function might not resolve *all* existing URL modificiations, but it has been tested on a vast, well \
        maintained variety of URLs. It typically resolves URL to the correct final page while avoiding redirects to \
        generic error pages.

    Usage::

        from pewtils.http import canonical_link

        >>> canonical_link("https://pewrsr.ch/2lxB0EX")
        "https://www.pewresearch.org/interactives/how-does-a-computer-see-gender/"

    """

    BAD_STATUS_CODES = [
        302,
        307,
        400,
        404,
        405,
        407,
        500,
        501,
        502,
        503,
        504,
        520,
        530,
        404,
    ]
    PROXY_REQUIRED = [307, 407]
    CHECK_LENGTH = [301, 302, 200, 404]

    close_session = False
    if not session:
        close_session = True
        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})
    if not url.startswith("http"):
        url = "http://" + url
    response = None
    try:
        with Timeout(timeout):
            try:
                response = session.head(url, allow_redirects=True, timeout=timeout)
            except requests.ConnectionError:
                try:
                    response = session.head(url, allow_redirects=False, timeout=timeout)
                except:
                    pass
    except:
        pass

    if response:

        history = [(h.status_code, h.url) for h in response.history]
        history.append((response.status_code, response.url))

        last_good_url = history[0][1]
        original_parsed = urlparse.urlparse(last_good_url)
        has_path = original_parsed.path not in ["/", ""]
        has_query = original_parsed.query != ""
        prev_was_shortener = False
        prev_path = None
        prev_query = None
        status_code = None
        for i, resp in enumerate(history):
            status_code, response_url = resp
            if "errors/404" in response_url:
                # If it's clearly a 404 landing page, stop and use the last observed good URL
                break
            parsed = urlparse.urlparse(response_url)
            if (
                parsed.netloc in VANITY_LINK_SHORTENERS.keys()
                or parsed.netloc in GENERAL_LINK_SHORTENERS
            ):
                # Don't consider known shortened URLs
                is_shortener = True
            else:
                is_shortener = False
            if not is_shortener:
                if i != 0:
                    for param, val in urlparse.parse_qs(parsed.query).items():
                        if len(val) == 1 and val[0].startswith("http"):
                            parsed_possible_url = urlparse.urlparse(val[0])
                            if (
                                parsed_possible_url.scheme
                                and parsed_possible_url.netloc
                            ):
                                # If the URL contains a GET parameter that is, itself, a URL, it's likely redirecting
                                # to it, so we're going to stop this run and start the process over with the new URL
                                return canonical_link(
                                    val[0],
                                    timeout=timeout,
                                    session=session,
                                    user_agent=user_agent,
                                )
                if status_code in PROXY_REQUIRED:
                    # These codes tend to indicate the last good URL in the chain
                    last_good_url = response_url
                    break
                good_path = not has_path or parsed.path not in ["/", ""]
                good_query = not has_query or parsed.query != ""
                # If the URL has a path or some GET parameters, we'll inspect further
                # Otherwise we just go with the previous URL
                # Link shorteners are very rarely used to reference root domains
                if good_query or good_path:
                    if (
                        re.sub("https", "http", response_url)
                        == re.sub("https", "http", last_good_url)
                        or parsed.path == original_parsed.path
                    ) or response_url.lower() == last_good_url.lower():
                        # If it's the same link but only the domain, protocol, or casing changed, it's fine
                        last_good_url = response_url
                    elif i != 0 and status_code in CHECK_LENGTH:
                        # For these codes, we're going to see how much the link changed
                        # Redirects and 404s sometimes preserve a decent URL, sometimes they go to a landing page
                        # The following cutoffs seem to do a good job most of the time:
                        # 1) The new URL has a long domain more than 7 characters, so it's not likely a shortened URL
                        # 2) The prior URL had a long path and this one has fewer than 20 characters and it wasn't
                        # swapped out for GET params
                        # 3) Or the prior URL had GET params and this one has far fewer and no replacement path
                        # If these conditions are met and the path or query do not identically match the prior link
                        # Then it's usually a generic error page
                        bad = False
                        if (
                            has_path
                            and len(parsed.netloc) > 7
                            and len(parsed.path) < 20
                            and len(parsed.query) == 0
                            and prev_path != parsed.path
                        ) or (
                            has_query
                            and len(parsed.netloc) > 7
                            and len(parsed.query) < 20
                            and len(parsed.path) <= 1
                            and prev_query != parsed.query
                        ):
                            bad = True
                        if not bad or prev_was_shortener:
                            last_good_url = response_url
                            # print("GOOD: {}, {}".format(status_code, response_url))
                        else:
                            # These can sometimes resolve further though, so we continue onward
                            prev_path = None
                            prev_query = None
                    else:
                        if status_code not in BAD_STATUS_CODES:
                            last_good_url = response_url
                        else:
                            break
                else:
                    # Resolved to a general URL
                    break

            prev_was_shortener = is_shortener
            prev_path = parsed.path
            prev_query = parsed.query

        if status_code not in BAD_STATUS_CODES:
            # If the URL ended on a good status code, we'll try to trim out any unnecessary GET parameters
            last_good_url = trim_get_parameters(
                last_good_url, session=session, timeout=timeout, user_agent=user_agent
            )

        url = last_good_url

    if close_session:
        session.close()

    return url
