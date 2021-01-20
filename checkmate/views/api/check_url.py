"""URL checking."""

from pyramid.httpexceptions import HTTPNoContent
from pyramid.view import view_config

from checkmate.checker.url import CompoundRules
from checkmate.exceptions import BadURLParameter
from checkmate.services import SecureLinkService


@view_config(route_name="check_url", renderer="json")
def check_url(request):
    """Check a given URL for any reasons we might want to block it."""

    try:
        url = request.GET["url"]
    except KeyError as err:
        raise BadURLParameter("url", "Parameter 'url' is required") from err

    checker = CompoundRules(request.db, allow_all=request.GET.get("allow_all"))
    reasons = list(checker.check_url(url))

    if not reasons:
        # If everything is fine give a 204 which is successful, but has no body
        return HTTPNoContent()

    # Reasons are in severity order, worst first
    worst_reason = reasons[0]

    # https://jsonapi.org/format/#document-top-level
    return {
        "data": [reason.serialise() for reason in reasons],
        "meta": {
            # Reasons are in severity order, worst first
            "maxSeverity": worst_reason.severity.value,
        },
        "links": {
            "html": request.find_service(SecureLinkService).route_url(
                "present_block", _query={"url": url, "reason": worst_reason.value}
            )
        },
    }
