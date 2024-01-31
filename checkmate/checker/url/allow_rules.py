"""A checker based on our own curated allow list."""

from checkmate.checker.url._hashed_url_checker import HashedURLChecker
from checkmate.models import AllowRule, Reason


class AllowRules(HashedURLChecker):
    """A checker based on our own curated allow list."""

    def check_url(self, hex_hashes):
        """Check to see if a URL is explicitly allowed, based on it's hashes.

        :param hex_hashes: A list of hashes for a URL
        :returns: A generator of Reason objects
        """

        hits = AllowRule.find_matches(self._session, hex_hashes)

        if not hits.count():
            yield Reason.NOT_ALLOWED
