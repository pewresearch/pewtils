import re


URL_REGEX = re.compile(
    r"((?:https?:\/\/(?:www\.)?)?[-a-zA-Z0-9@:%._\+~#=]{2,4096}\.[a-z]{2,6}\b(?:[-a-zA-Z0-9@:%_\+.~#?&//=]*))"
)

DOMAIN_REGEX = re.compile(
    r"(?:http[s]?\:\/\/)?(?:www(?:s?)\.)?([\w\.\-]+)(?:[\\\/](?:.+))?"
)

HTTP_REGEX = re.compile(r"^http(?:s)?\:\/\/")

US_DOLLAR_REGEX = re.compile(
    r"(\$(?:[1-9][0-9]{0,2}(?:(?:\,[0-9]{3})+)?(?:\.[0-9]{1,2})?))\b"
)
TITLEWORD_REGEX = re.compile(r"\b([A-Z][a-z]+)\b")
NUMBER_REGEX = re.compile(r"\b([0-9]+)\b")
NONALPHA_REGEX = re.compile(r"[^\w]")
