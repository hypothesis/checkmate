"""A checker based on our own curated allow list."""

from checkmate.checker.url.reason import Reason
from checkmate.models.db.allow_rule import AllowRule


class AllowRules:
    """A checker based on our own curated allow list."""

    def __init__(self, session):
        """Create a new AllowRules object.

        :param session: A DB session to work in
        """
        self._session = session

    def check_url(self, hex_hashes):
        """Check to see if a URL is explicitly allowed, based on it's hashes.

        :param hex_hashes: A list of hashes for a URL
        :returns: A generator of Reason objects
        """

        hits = AllowRule.find_matches(self._session, hex_hashes)

        if not hits.count():
            yield Reason.NOT_ALLOWED
