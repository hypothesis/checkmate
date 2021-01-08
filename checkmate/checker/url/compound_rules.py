from operator import attrgetter

from checkmate.checker.url.allow_rules import AllowRules
from checkmate.checker.url.custom_rules import CustomRules
from checkmate.checker.url.url_haus import URLHaus
from checkmate.models import Severity
from checkmate.url import hash_url


class CompoundRules:
    """A wrapper around other checking rules."""

    def __init__(self, db_session, allow_all=False, fail_fast=True):
        """Create a new CompoundRules object.

        :param db_session: A DB session to work in
        :param allow_all: Disable the allow list protection
        :param fail_fast: Stop at the first mandatory reason we get
        """
        self._db_session = db_session
        self._fail_fast = fail_fast

        self._checkers = [URLHaus, CustomRules]
        if not allow_all:
            self._checkers.append(AllowRules)

    def check_url(self, url):
        """Check for reasons to block a URL based on it's hashes.

        :param url: URL to check
        :returns: A generator of Reason objects (most severe first)
        """

        url_hashes = list(hash_url(url))

        # Use a set to weed out repeated identifications
        reasons = set()

        for checker in self._checkers:
            reasons.update(checker(self._db_session).check_url(url_hashes))

            # We don't need to keep searching the database if we've already
            # been told this is a mandatory block
            if self._fail_fast and self._has_mandatory(reasons):
                break

        # Sort the reasons by worst first
        return reversed(sorted(reasons, key=attrgetter("severity")))

    @classmethod
    def _has_mandatory(cls, reasons):
        for reason in reasons:
            if reason.severity == Severity.MANDATORY:
                return True

        return False
