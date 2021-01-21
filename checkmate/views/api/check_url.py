"""URL checking."""

from pyramid.httpexceptions import HTTPNoContent
from pyramid.view import view_config

from checkmate.exceptions import BadURLParameter, MalformedURL
from checkmate.services import SecureLinkService, URLCheckerService


@view_config(route_name="check_url", renderer="json")
def check_url(request):
    """Check a given URL for any reasons we might want to block it."""

    try:
        url = request.GET["url"]
    except KeyError as err:
        raise BadURLParameter("url", "Parameter 'url' is required") from err

    url_checker = request.find_service(URLCheckerService)

    try:
        reasons = list(
            url_checker.check_url(url, allow_all=request.GET.get("allow_all"))
        )
    except MalformedURL as err:
        raise BadURLParameter("url", "Parameter 'url' isn't valid") from err

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
