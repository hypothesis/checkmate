import re
from urllib.parse import urlparse


class ExpandURL:
    IPV4 = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")

    @classmethod
    def expand(cls, normalised_url):
        parsed = urlparse(normalised_url)

        path_variants = tuple(cls.vary_path(parsed.path, parsed.query))

        for host in cls.vary_hostname(parsed.netloc):
            for path in path_variants:
                yield host + path

    @classmethod
    def vary_hostname(cls, hostname):
        yield hostname

        if cls.IPV4.match(hostname):
            return

        parts = hostname.split(".")
        start = max(len(parts) - 5, 1)
        for pos in range(start, len(parts) - 1):
            yield ".".join(parts[pos:])

    @classmethod
    def vary_path(cls, path, query):
        if query:
            yield path + "?" + query

        yield path

        parts = path.rstrip("/").split("/")
        max_parts = min(len(parts), 5)
        for pos in range(1, max_parts):
            yield "/".join(parts[:pos]) + "/"
