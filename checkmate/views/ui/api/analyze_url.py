from urllib.parse import urlunparse

from pyramid.view import view_config

from checkmate.exceptions import BadURLParameter
from checkmate.models import Principals
from checkmate.services import URLCheckerService
from checkmate.url import CanonicalURL, Domain


@view_config(
    route_name="analyze_url", renderer="json", effective_principals=[Principals.STAFF]
)
def analyze_url(request):
    """Detailed feedback on a URL for the admin pages."""

    try:
        url = request.GET["url"]
    except KeyError as err:
        raise BadURLParameter("url", "Parameter 'url' is required") from err

    url_checker = request.find_service(URLCheckerService)
    detections = url_checker.check_url(url)

    scheme, netloc, path, params, query, _fragment = CanonicalURL.canonical_split(url)
    canonical_url = urlunparse([scheme, netloc, path, params, query, None])

    if params:
        # Path params are weird, and you don't see them often. They aren't
        # query params so we'll treat them as part of the path
        path += ";" + params

    domain = Domain(netloc)

    sub_domains, root_domain = domain.split_domain()

    return {
        "type": "url",
        "id": canonical_url,
        "attributes": {
            "scheme": scheme,
            "subDomains": sub_domains,
            "rootDomain": root_domain,
            "path": path,
            "query": query,
        },
        "meta": {
            "isValid": domain.is_valid,
            "isIPv4": domain.is_ip_v4,
            "isPublic": domain.is_public,
        },
        "links": {"canonical": canonical_url, "raw": url},
        "relationships": {
            "detections": {"data": [detection.serialise() for detection in detections]}
        },
    }
