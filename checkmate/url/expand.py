"""An implementation of Google Web Risk suffix/prefix expressions."""
import re
from urllib.parse import urlparse


class ExpandURL:
    """Expand a URL into variations for comparison.

    As defined in: https://cloud.google.com/web-risk/docs/urls-hashing#suffixprefix_expressions
    """

    IPV4 = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")

    @classmethod
    def expand(cls, normalised_url):
        """Expand a URL into many versions for comparison.

        This will:

         * Remove the scheme and "://"
         * Progressively remove parts from the start of the domain
         * Progressively simplify the path

        :param normalised_url: A pre-normalised URL to vary
        :returns: A generator of domain suffix, path prefix variations
        """
        parsed = urlparse(normalised_url)

        path_variants = tuple(cls._vary_path(parsed.path, parsed.query))

        for host in cls._vary_hostname(parsed.netloc):
            for path in path_variants:
                yield host + path

    @classmethod
    def expand_single(cls, normalised_url):
        """Create a single expansion of the URL.

        This allows you to create the least simplified version of the
        expansions to use to create rules for comparing with.
        """
        parsed = urlparse(normalised_url)

        return normalised_url.replace(parsed.scheme + "://", "")

    @classmethod
    def _vary_hostname(cls, hostname):
        yield hostname

        # Don't snip of bits of a IP address thinking it's a domain name
        if cls.IPV4.match(hostname):
            return

        # Progressively snip things from the left a maximum of 4 times,
        # starting from something which has a maximum of 5 components even if
        # the original domain has more
        parts = hostname.split(".")
        start = max(len(parts) - 5, 1)
        for pos in range(start, len(parts) - 1):
            yield ".".join(parts[pos:])

    @classmethod
    def _vary_path(cls, path, query):
        if query:
            yield path + "?" + query

        yield path

        # Build the path up from the start a maximum of 4 times
        parts = path.rstrip("/").split("/")
        max_parts = min(len(parts), 5)
        for pos in range(1, max_parts):
            yield "/".join(parts[:pos]) + "/"
