import re


URL_REGEX = re.compile(
    r"((?:https?:\/\/(?:www\.)?)?[-a-zA-Z0-9@:%._\+~#=]{1,4096}\.[a-z]{2,6}\b(?:[-a-zA-Z0-9@:%_\+.~#?&//=]*))"
)
"""
A compiled regular expression for extracting (probably) valid URLs.
"""

DOMAIN_REGEX = re.compile(
    r"(?:http[s]?\:\/\/)?(?:www(?:s?)\.)?([\w\.\-]+)(?:[\\\/](?:.+))?"
)
"""
A compiled regular expression for extracting domains from URLs. Can be useful in a pinch but we recommend \
using the :py:func:`pewtils.http.extract_domain_from_url` instead.
"""

HTTP_REGEX = re.compile(r"^http(?:s)?\:\/\/")
"""
A compiled regular expression for finding HTTP/S prefixes.
"""

US_DOLLAR_REGEX = re.compile(
    r"(\$(?:[1-9][0-9]{0,2}(?:(?:\,[0-9]{3})+)?(?:\.[0-9]{1,2})?))\b"
)
"""
A compiled regular expression finding USD monetary amounts.
"""

TITLEWORD_REGEX = re.compile(r"\b([A-Z][a-z]+)\b")
"""
A compiled regular expression for finding basic title-cased words.
"""

NUMBER_REGEX = re.compile(r"\b([0-9]+)\b")
"""
A compiled regular expression for finding raw numbers.
"""

NONALPHA_REGEX = re.compile(r"[^\w]")
"""
A compiled regular expression for finding non-alphanumeric values.
"""
