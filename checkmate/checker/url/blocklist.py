"""The abstract blocklist object."""

import fnmatch
import os
import re
from logging import getLogger
from urllib.parse import urlparse

from checkmate.checker.url.reason import Reason
from checkmate.exceptions import MalformedURL
from checkmate.url import canonicalize
from checkmate.url.canonicalize import CanonicalURL


class Blocklist:
    """A blocklist which URLs can be checked against.

    For details of how to change the blocklist see:
      * https://stackoverflow.com/c/hypothesis/questions/102/250

    And is downloaded locally, via supervisor using `bin/fetch-blocklist`
    """

    LOG = getLogger(__name__)

    # viahtml is ok with video, as far as we can tell
    PERMITTED = (Reason.MEDIA_VIDEO,)

    def __init__(self, filename):
        self.LOG.debug("Monitoring blocklist file '%s'", filename)

        self._filename = filename
        self._last_modified = None
        self.domains = {}
        self.patterns = {}

        self._refresh()

    def check_url(self, url):
        """Test the URL and return a list of reasons it should be blocked.

        :param url: URL to test
        :raise MalformedURL: If the URL cannot be parsed
        :return: An iterable of Reason objects (which may be empty)
        """
        self._refresh()

        domain = self._domain(url)
        if not domain:
            raise MalformedURL(f"The URL: '{url}' has no domain to check")

        blocked = self.domains.get(domain)
        if blocked:
            yield blocked

        for pattern, reason in self.patterns.items():
            if pattern.match(domain):
                yield reason

    def clear(self):
        """Remove all domains from the blocklist."""
        self.domains, self.patterns = {}, {}

    def add_domain(self, domain, reason):
        """Add a domain (or domain pattern) to the blocklist."""

        reason = Reason.parse(reason)
        if reason in self.PERMITTED:
            # This is listed as blocked, but this service can actually
            # serve this type without incident
            return

        if "*" in domain:
            # Convert a string with '*' wildcards into a regex
            pattern = re.compile(fnmatch.translate(domain), re.IGNORECASE)
            self.patterns[pattern] = reason
        else:
            self.domains[domain] = reason

    @classmethod
    def _domain(cls, url):
        return CanonicalURL.canonical_split(url)[1] or None

    def _refresh(self):
        if self._file_changed:
            self.LOG.debug("Reloading blocklist file")

            self.clear()
            for domain, reason in self._parse(self._filename):
                self.add_domain(domain, reason)

    @property
    def _file_changed(self):
        if not os.path.exists(self._filename):
            self.LOG.warning("Cannot find blocklist file '%s'", self._filename)
            return False

        last_modified = os.stat(self._filename).st_mtime
        if last_modified != self._last_modified:
            self._last_modified = last_modified
            return True

        return False

    LINE_PATTERN = re.compile(r"^(\S+)\s+(\S+)(?:\s*#.*)?$")

    @classmethod
    def _parse(cls, filename):
        with open(filename) as handle:
            for line in handle:
                line = line.strip()

                if not line or line.startswith("#"):
                    # Empty or comment line.
                    continue

                match = cls.LINE_PATTERN.match(line)
                if match:
                    domain, reason = match.group(1), match.group(2)
                else:
                    cls.LOG.warning("Cannot parse blocklist file line: '%s'")
                    continue

                yield domain, reason
