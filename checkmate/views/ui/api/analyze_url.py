from pyramid.view import view_config

from checkmate.exceptions import BadURLParameter
from checkmate.url import CanonicalURL
from urllib.parse import urlunparse


@view_config(route_name="analyze_url", renderer="json")
def analyze_url(request):
    """Detailed feedback on a URL for the admin pages."""

    try:
        url = request.GET["url"]
    except KeyError as err:
        raise BadURLParameter("url", "Parameter 'url' is required") from err

    variations = dict(_variations(url))

    return {
        "url": url,
        "variations": variations
    }


def _variations(url):
    scheme, netloc, path, params, query, _fragment = CanonicalURL.canonical_split(
        url)

    yield "domain", urlunparse([scheme, netloc, '', '', '', ''])

    if path and path != '/':
        yield "path", urlunparse([scheme, netloc, path, params, '', ''])

    if query:
        yield "full", urlunparse([scheme, netloc, path, params, query, ''])