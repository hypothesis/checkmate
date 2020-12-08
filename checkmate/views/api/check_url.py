"""URL checking."""
from operator import attrgetter

from pyramid.httpexceptions import HTTPNoContent
from pyramid.view import view_config

from checkmate.checker.url.blocklist import Blocklist
from checkmate.checker.url.custom_rules import CustomRules
from checkmate.exceptions import BadURLParameter, MalformedURL
from checkmate.url import hash_url


@view_config(route_name="check_url", renderer="json")
def check_url(request):
    """Check a given URL for any reasons we might want to block it."""

    try:
        url = request.GET["url"]
    except KeyError as err:
        raise BadURLParameter("url", "Parameter 'url' is required") from err

    url_hashes = list(hash_url(url))

    # Use a set to weed out repeated identifications
    reasons = set()

    # Update with reasons from our private list file
    try:
        reasons.update(request.registry.url_blocklist.check_url(url))
    except MalformedURL as err:
        raise BadURLParameter("url", err.args[0]) from err

    # Update with reasons from our private list table
    reasons.update(CustomRules(request.db).check_url(url_hashes))

    # Update with reasons from other services?
    ...

    if not reasons:
        # If everything is fine give a 204 which is successful, but has no body
        return HTTPNoContent()

    # Sort the reasons by worst first
    ordered_reasons = list(reversed(sorted(reasons, key=attrgetter("severity"))))

    # https://jsonapi.org/format/#document-top-level
    return {
        "data": [reason.serialise() for reason in ordered_reasons],
        "meta": {
            "maxSeverity": ordered_reasons[0].severity.value,
        },
    }


def includeme(config):  # pragma: no cover
    """Pyramid config."""

    # We need this to be full global, so we don't re-read the file on every
    # request. So we'll follow the suggestion here:
    # https://stackoverflow.com/questions/62513766/connection-pool-to-external-services-redis-in-pyramid
    config.registry.url_blocklist = Blocklist(
        config.registry.settings["checkmate_blocklist_path"]
    )
