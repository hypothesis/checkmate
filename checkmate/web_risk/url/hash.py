from checkmate.web_risk.url.canonicalise import CanonicalURL
from checkmate.web_risk.url.expand import ExpandURL

from hashlib import sha256


def hash_url(url, bytes=None):
    if bytes is None:
        bytes = 32

    url = CanonicalURL.canonicalise(url)
    for variant in ExpandURL.expand(url):
        digest = sha256(variant.encode('ascii'))

        yield digest.digest()[:bytes]