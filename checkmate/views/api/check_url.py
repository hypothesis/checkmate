"""URL checking."""
from operator import attrgetter

from pyramid.httpexceptions import HTTPNoContent
from pyramid.view import view_config

from checkmate.checker.url import CustomRules, URLHaus
from checkmate.exceptions import BadURLParameter
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
    reasons = set(CustomRules(request.db).check_url(url_hashes))
    reasons.update(URLHaus(request.db).check_url(url_hashes))

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
