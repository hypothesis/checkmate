from operator import attrgetter

from checkmate.checker.url import AllowRules, CustomRules, URLHaus
from checkmate.models import Detection, Severity, Source
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

    def check_url(self, url, allow_all=False, fail_fast=True, ignore_reasons=None):
        """Check for reasons to block a URL based on it's hashes.

        :param url: URL to check
        :param allow_all: Disable the allow list protection
        :param fail_fast: Stop at the first mandatory reason we get
        :param ignore_reasons: Ignore this list of reasons
        :returns: A generator of Detection objects (most severe first)
        """

        url_hashes = list(hash_url(url))
        detections = self._get_detections(
            url_hashes, allow_all, fail_fast, ignore_reasons or []
        )

        # Sort the detections by worst first
        return reversed(sorted(detections, key=attrgetter("severity")))

    def _get_detections(self, url_hashes, allow_all, fail_fast, ignore_reasons):
        detections = []

        for source, checker in self._get_checkers(allow_all):
            for reason in checker.check_url(url_hashes):
                if reason in ignore_reasons:
                    continue

                detections.append(Detection(reason, source))

                # We don't need to keep searching the database if we've already
                # been told this is a mandatory block
                if fail_fast and reason.severity == Severity.MANDATORY:
                    return detections

        return detections

    def _get_checkers(self, allow_all):
        yield from self._blocking_checkers.items()

        if not allow_all:
            yield from self._allowing_checkers.items()


def factory(_context, request):
    return URLCheckerService(db_session=request.db)
