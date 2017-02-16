from __future__ import print_function
from __future__ import division
from builtins import str
import re, time, threading

from functools import wraps
from random import uniform
from bs4 import BeautifulSoup
from unidecode import unidecode

from pewtils import get_hash, decode_text


def hash_url(url):
    '''
    Clears out http/https prefix and returns an MD5 hash of the URL

    :param url: string of the url
    :return: hashed string
    '''
    http_regex = re.compile(r'^http(s)?\:\/\/')
    return get_hash(unidecode(http_regex.sub('', url.lower())), hash_function="md5")


def new_random_number(attempt = 1, base_interval = 1.0, max_sleep = 10):

    '''
    Generate a variable waiting time in seconds which exponentially increases with each attempt. \
    Note that this function does NOT itself sleep or block execution, it just adds new_random_number to your timer.

    :param attempt: Increasing attempt will probably raise the sleep interval.
    :param base_interval: The minimum time. Must be greater than zero.
    :param max_sleep: The maximum amount of time allowed.
    :return: Seconds to sleep
    '''

    return uniform(0, min(max_sleep, base_interval * 2 ** attempt))






def strip_html(html, simple=False, break_tags=None):
    """
    Removes anything between </> tags

    :param text: String to filter
    :return: String with HTML tags removed
    """

    if not break_tags:
        break_tags = ["strong", "em", "i", "b", "p"]
    if not simple:
        try:

            split_re = re.compile(r'\s{2,}')
            soup = BeautifulSoup(html, "lxml")
            for tag in soup():
                if ("class" in tag.attrs and ("menu" in tag.attrs["class"] or "header" in tag.attrs["class"])) or \
                        ("menu" in str(tag.id) or "header" in str(tag.id)):
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
            text = re.sub(r'(\sA){2,}\s', ' ', text)
            text = re.sub("\n+(\s+)?", "\n\n", text)
            text = re.sub(" +", " ", text)
            text = re.sub("\t+", " ", text)

            return text

        except Exception as e:

            print("strip_html error")
            print(e)
            text = re.sub("<[^>]*>", " ",
                          re.sub("\\s+", " ", html)
                          ).strip()
            return text

    else:
        return "\n".join([
            re.sub(r"\s+", " ", re.sub(r"\<[^\>]+\>", " ", section)) for section in
                re.sub(r"\<\/?div\>|\<\/?p\>|\<br\>", "\n", html).split("\n")
        ])


LINK_SHORTENER_MAP = {
    "wapo.st": "washingtonpost.com",
    "nyti.ms": "nytimes.com",
    "fxn.ws": "foxnews.com",
    "wh.gov": "whitehouse.gov",
    "goo.gl": "google.com",
    "huff.to": "huffingtonpost.com",
    "n.pr": "npr.org",
    "apne.ws": "apnews.com",
    "ap.org": "apnews.com",
    "youtu.be": "youtube.com",
    "washex.am": "washingtonexaminer.com",
    "wpo.st": "washingtonpost.com",
    "usat.ly": "usatoday.com",
    "cbsloc.al": "cbslocal.com",
    "cbsn.ws": "cbsnews.com",
    "bloom.bg": "bloomberg.com",
    "abcn.ws": "abcnews.com",
    "reut.rs": "reuters.com",
    "ti.me": "time.com",
    "politi.co": "politico.com",
    "cnn.it": "cnn.com",
    "cs.pn": "c-span.org",
    "t.co": "twitter.com",
    "bzfd.it": "buzzfeed.com",
    "c-spanvideo.org": "c-span.org",
    "lat.ms": "latimes.com",
    "nbcnews.to": "nbcnews.com",
    "onforb.es": "forbes.com",
    "theatln.tc": "theatlantic.com",
    "yhoo.it": "yahoo.com",
    "sen.gov": "senate.gov",
    "es.pn": "espn.com",
    "dot.gov": "transportation.gov",
    "wrd.cm": "wired.com",
    "cour.at": "courant.com",
    "read.bi": "businessinsider.com",
    "dailysign.al": "dailysignal.com",
    "cnnmon.ie": "cnn.com",
    "cnb.cx": "cnbc.com",
    "atxne.ws": "statesman.com",
    "slate.me": "slate.com",
    "detne.ws": "detroitnews.com",
    "huffpost.com": "huffingtonpost.com",
    "injo.com": "ijr.com",
    "fb.me": "facebook.com",
    "amzn.to": "amazon.com",
    "fb.com": "facebook.com",
    "lnkd.in": "linkedin.com",
    "mailchi.mp": "mailchimp.com",
    "hrld.us": "miamiherald.com",
    "oh.us": "state.oh.us",
    "ofa.bo": "ofa.us",
    "indy.st": "indystar.com",
    "strib.mn": "startribune.com",
    "nydn.us": "nydailynews.com",
    "bsun.md": "baltimoresun.com",
    "bayareane.ws": "eastbaytimes.com",
    "pa.us": "state.pa.us",
    "g.co": "google.com",
    "mn.us": "state.mn.us",
    "thebea.st": "thedailybeast.com",
    "dmreg.co": "desmoinesregister.com",
    "bernie.to": "berniesanders.com",
    "dpo.st": "denverpost.com",
    "delonline.us": "delawareonline.com",
    "fb.me": "facebook.com",
    "azc.cc": "azcentral.com",
    "ptrtvoic.es": "patriotvoices.com",
    "cjky.it": "courier-journal.com",
    "md.us": "state.md.us",
    "goldenisles.news": "thebrunswicknews.com",
    "ohne.ws": "newarkadvocate.com",
    "thkpr.gs": "thinkprogress.org",
    "hrld.us": "miamiherald.com",
    "ma.us": "state.ma.us",
    "ny.us": "state.ny.us",
    "nm.us": "state.nm.us",
    "huffpost.com": "huffingtonpost.com"
}
