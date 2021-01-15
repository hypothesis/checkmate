"""User feedback for blocked pages."""
from urllib.parse import urlparse

from pyramid.exceptions import HTTPForbidden
from pyramid.view import view_config

from checkmate.services import SecureLinkService


@view_config(
    route_name="present_block",
    renderer="checkmate:templates/blocked_page.html.jinja2",
    # The content of a given page should never change once issued. It should
    # be possible to cache them indefinitely, but we want something a bit
    # shorter than "forever" so we can modify the page without too much
    # delay.
    http_cache=(3600, {"public": 1}),
)
def present_block(_context, request):
    """Render an HTML version of a blocked URL with explanation."""

    if not request.find_service(SecureLinkService).is_secure(request):
        raise HTTPForbidden()

    # At this point we know the contents of the args came from us, so we'll
    # assume that they are correct.
    url_to_annotate = request.GET["url"]

    return {
        "blocked_url": url_to_annotate,
        "domain_to_annotate": urlparse(url_to_annotate).netloc,
        "reason": request.GET["reason"],
    }
