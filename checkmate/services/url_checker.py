from operator import attrgetter

from checkmate.checker.url import AllowRules, CustomRules, URLHaus
from checkmate.models import Severity
from checkmate.models.source import Source
from checkmate.url import hash_url


class URLCheckerService:
    """A wrapper around other checking rules."""

    def __init__(self, db_session):
        """Create a new CompoundRules object.

        :param db_session: A DB session to work in
        """
        self._db_session = db_session
        self._blocking_checkers = {
            Source.URL_HAUS: URLHaus(db_session),
            Source.BLOCK_LIST: CustomRules(db_session),
        }
        self._allowing_checkers = {
            Source.ALLOW_LIST: AllowRules(db_session),
        }

    def check_url(self, url, allow_all=False, fail_fast=True):
        """Check for reasons to block a URL based on it's hashes.

        :param url: URL to check
        :param allow_all: Disable the allow list protection
        :param fail_fast: Stop at the first mandatory reason we get
        :returns: A generator of Reason objects (most severe first)
        """

        url_hashes = list(hash_url(url))

        # Use a set to weed out repeated identifications
        reasons = set()

        for _source, checker in self._get_checkers(allow_all):
            reasons.update(checker.check_url(url_hashes))

            # We don't need to keep searching the database if we've already
            # been told this is a mandatory block
            if fail_fast and self._has_mandatory(reasons):
                break

        # Sort the reasons by worst first
        return reversed(sorted(reasons, key=attrgetter("severity")))

    def _get_checkers(self, allow_all):
        yield from self._blocking_checkers.items()

        if not allow_all:
            yield from self._allowing_checkers.items()

    @classmethod
    def _has_mandatory(cls, reasons):
        for reason in reasons:
            if reason.severity == Severity.MANDATORY:
                return True

        return False


def factory(_context, request):
    return URLCheckerService(db_session=request.db)
