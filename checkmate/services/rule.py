from checkmate.exceptions import ResourceConflict
from checkmate.models import AllowRule, Detection, Reason, Source
from checkmate.services.url_checker import URLCheckerService
from checkmate.url import hash_for_rule


class RuleService:
    """A service for interacting with rules themselves."""

    _ALLOW_LIST_DETECTION = Detection(Reason.NOT_ALLOWED, Source.ALLOW_LIST)

    def __init__(self, checker, db):
        """Initialise the service.

        :param checker: Instance of URLCheckerService
        :param db: DB session object
        """
        self._checker = checker
        self._db = db

    def add_to_allow_list(self, url):
        """Add a given URL to the allow list.

        This will also check to see if this is:

         * Already allowed
         * On any of our block lists

        :param url: URL to allow
        :raises ResourceConflict: If the URL cannot be allowed for any reason
        """
        reasons = list(self._checker.check_url(url, fail_fast=False))

        try:
            reasons.remove(self._ALLOW_LIST_DETECTION)
        except ValueError:
            raise ResourceConflict("Requested URL is already allowed") from None

        if reasons:
            raise ResourceConflict(
                f"Cannot allow URL as reasons to block found: {reasons}"
            )

        rule_string, hex_hash = hash_for_rule(url)

        rule = AllowRule(rule=rule_string, hash=hex_hash, tags=["manual"])
        self._db.add(rule)
        self._db.flush()

        return rule


def factory(_context, request):
    return RuleService(request.find_service(URLCheckerService), request.db)
