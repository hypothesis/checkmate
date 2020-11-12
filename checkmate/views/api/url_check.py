"""URL checking."""
from pyramid.httpexceptions import HTTPNoContent
from pyramid.view import view_config


@view_config(route_name="url_check")
def url_check(_request):
    """Check a given URL for any reasons we might want to block it."""

    # If everything is fine give a 204 which is successful, but has no body
    return HTTPNoContent()
