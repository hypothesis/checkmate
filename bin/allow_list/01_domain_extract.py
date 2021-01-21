"""Script to extract domains from a dump of H 'URL's."""

import re
from collections import Counter
from urllib.parse import unquote

from bin.allow_list.file_tools import load_json, load_text, save_text
from checkmate.url import CanonicalURL, Domain


class InvalidURL(Exception):
    def __init__(self, url_part, value, reason=None):
        self.url_part = url_part
        self.reason = reason
        self.value = value

        super().__init__(f"Bad {url_part}: {reason}")


class DomainExtractor:
    GOOD_SCHEME = {"http", "https"}
    BAD_SCHEME = set(load_json("data/bad_url_schemes.json"))

    LEADING_REPLACEMENTS = {
        "https://https//": "http://",
        "http://http//": "http://",
        "http/": "http://",
        "http://%20http://": "http://",
        "http://%20http//": "http://",
        "http://%20https//": "http://",
        "http://https://": "https://",
        "https://http//": "http://",
        "http://httpl//": "http://",
        "httpss://": "http://",
        "htts://": "http://",
        "http:/-": "http://",
        "ttps://": "http://",
        "//": "http://",
        "url=": "",
    }

    LEADING_BLOB_RE = re.compile("^blob:")
    LEADING_ABOUT_READER_RE = re.compile(r"^about:reader\?url=")

    @classmethod
    def extract_domain(cls, url):
        # Some of our URLs are quoted for some reason
        url = cls._fix_url(url)
        scheme, domain = cls._canonical_split(url)

        if scheme in cls.BAD_SCHEME:
            raise InvalidURL("scheme", scheme, "known_bad")

        if scheme not in cls.GOOD_SCHEME:
            raise InvalidURL("scheme", scheme, "unknown")

        domain = Domain(domain)

        if domain.endswith(".pdf") or domain.endswith(".txt"):
            raise InvalidURL("domain", domain, "file")

        if not domain.is_valid:
            raise InvalidURL("domain", domain, "invalid")

        if not domain.is_public:
            raise InvalidURL("domain", domain, "not_public")

        return domain

    @classmethod
    def _fix_url(cls, url):
        """Attempt to fix a number of the mangled versions of URLs we have."""

        # Looks like a bytes dump
        if url.startswith("b'"):
            url = url.lstrip("b")

        # Some of our URLs are quoted for some reason
        for start, end in (('"', '"'), ("'", "'"), ("(", ")")):
            if url.startswith(start) and url.endswith(end):
                url = url.lstrip(start).rstrip(end)

        # Some of our urls have 'blob:' at the front
        if cls.LEADING_BLOB_RE.match(url):
            url = cls.LEADING_BLOB_RE.sub("", url)

            # The blobs seem to be URL encoded
            url = unquote(url)

        # Very similar some have "about:reader?url="
        if cls.LEADING_ABOUT_READER_RE.match(url):
            url = cls.LEADING_ABOUT_READER_RE.sub("", url)

            # The blobs seem to be URL encoded
            url = unquote(url)

        # Some weird mangled things we can recover from
        for prefix, replacement in cls.LEADING_REPLACEMENTS.items():
            if url.startswith(prefix):
                url = replacement + url[len(prefix) :]

        return url

    @classmethod
    def _canonical_split(cls, url):
        # An absolute path
        if url.startswith("/"):
            raise InvalidURL("url", url, "absolute_path")

        # A relative path
        if url.startswith("../"):
            raise InvalidURL("url", url, "relative_path")

        # These confuse our URL parser and don't come out as a scheme
        if url.startswith("doi:"):
            raise InvalidURL("scheme", "doi")

        try:
            parts = CanonicalURL.canonical_split(url)
            # Just the scheme and domain
            return parts[0], parts[1]

        except Exception as err:
            raise InvalidURL("url", url, "parse_error") from err


if __name__ == "__main__":
    source_file = "process/01_h_urls.txt"

    domains = set()
    counts = Counter()

    bad_count = 0
    for count, url in enumerate(load_text(source_file)):
        try:
            domain = DomainExtractor.extract_domain(url)
            domains.update({domain: 1})
            counts.update({"ok": 1})

        except InvalidURL as err:
            counts.update({"error": 1})

        if count % 10000 == 0:
            print(dict(counts))

    save_text("process/02_domains.txt", domains)
