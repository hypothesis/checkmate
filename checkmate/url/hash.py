"""Implementation of Google Web Risk URL hashing.

As defined here: https://cloud.google.com/web-risk/docs/urls-hashing#hash_computations
"""

from hashlib import sha256

from checkmate.url.canonicalize import CanonicalURL
from checkmate.url.expand import ExpandURL

# This is all very speculation based at this point, we're not sure how this
# is going to look until we have our hands on some data.


def hash_url(raw_url):  # pragma: no cover
    """Create multiple hashed variations of a URL to check."""

    canonical_url = CanonicalURL.canonicalize(raw_url)

    for variant in ExpandURL.expand(canonical_url):
        digest = sha256(variant.encode("ascii"))

        yield digest.hexdigest()


def hash_for_rule(raw_url):  # pragma: no cover
    """Create a full hash of a URL for to compare against."""

    canonical_url = CanonicalURL.canonicalize(raw_url)
    expanded_url = ExpandURL.expand_single(canonical_url)

    digest = sha256(expanded_url.encode("ascii"))

    return expanded_url, digest.hexdigest()
