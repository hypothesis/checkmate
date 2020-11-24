"""Implementation of Google Web Risk URL hashing.

As defined here: https://cloud.google.com/web-risk/docs/urls-hashing#hash_computations
"""

from hashlib import sha256

from checkmate.url.canonicalize import CanonicalURL
from checkmate.url.expand import ExpandURL

# This is all very speculation based at this point, we're not sure how this
# is going to look until we have our hands on some data.


def hash_url(url, num_bytes=None):  # pragma: no cover
    """Create multiple hashed variations of a URL to check."""

    if num_bytes is None:
        num_bytes = 32

    url = CanonicalURL.canonicalize(url)

    for variant in ExpandURL.expand(url):
        digest = sha256(variant.encode("ascii"))

        yield digest.digest()[:num_bytes]


def hash_for_rule(url):  # pragma: no cover
    """Create a full hash of a URL for to compare against."""

    url = CanonicalURL.canonicalize(url)
    url = ExpandURL.expand_single(url)

    digest = sha256(url.encode("ascii"))

    return digest.digest()
