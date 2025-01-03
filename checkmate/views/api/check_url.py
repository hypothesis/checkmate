"""URL checking."""

import logging

from pyramid.httpexceptions import HTTPNoContent
from pyramid.view import view_config

from checkmate.exceptions import BadURL, BadURLParameter
from checkmate.models import BlockedFor, Reason, Source
from checkmate.security import Permissions
from checkmate.services import SecureLinkService, URLCheckerService

logger = logging.getLogger(__name__)


@view_config(route_name="check_url", renderer="json", permission=Permissions.CHECK_URL)
def check_url(request):
    """Check a given URL for any reasons we might want to block it."""

    try:
        url = request.GET["url"]
    except KeyError as err:
        raise BadURLParameter("url", "Parameter 'url' is required") from err

    ignore_reasons = request.GET.get("ignore_reasons", [])
    if ignore_reasons:
        try:
            ignore_reasons = set(
                Reason.parse(reason, default=None)
                for reason in ignore_reasons.split(",")
            )
        except ValueError as err:
            raise BadURLParameter(
                "ignored_reasons", "Parameter 'ignored_reasons' contains unknown value"
            ) from err

    url_checker = request.find_service(URLCheckerService)

    try:
        detections = list(
            url_checker.check_url(
                url,
                allow_all=request.GET.get("allow_all"),
                ignore_reasons=ignore_reasons,
            )
        )
    except BadURL as err:
        raise BadURLParameter("url", "Parameter 'url' isn't valid") from err

    if not detections:
        # If everything is fine give a 204 which is successful, but has no body
        logger.info(
            "Access allowed for URL %r via source %s", url, Source.ALLOW_LIST.value
        )
        return HTTPNoContent()

    # Get unique reasons mapped to corresponding detections
    reasons = {detection.reason: detection for detection in detections}

    # Reasons are ordered, worst first
    worst_reason = min(reasons)
    logger.info(
        "Access blocked for URL %r via source %s due to reason %s",
        url,
        reasons[worst_reason].source.value,
        worst_reason.value,
    )

    blocked_for = request.GET.get("blocked_for", BlockedFor.GENERAL.value)

    # https://jsonapi.org/format/#document-top-level
    return {
        "data": [reason.serialise() for reason in sorted(reasons)],
        "meta": {
            # Reasons are in severity order, worst first
            "maxSeverity": worst_reason.severity.value,
        },
        "links": {
            "html": request.find_service(SecureLinkService).route_url(
                "present_block",
                _scheme=request.registry.settings["public_scheme"],
                _port=request.registry.settings["public_port"],
                _host=request.registry.settings["public_host"],
                _query={
                    "url": url,
                    "reason": worst_reason.value,
                    "blocked_for": blocked_for,
                },
            )
        },
    }
