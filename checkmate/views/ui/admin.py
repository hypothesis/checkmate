"""User feedback for blocked pages."""
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from checkmate.models import Principals


@view_config(
    route_name="admin_pages",
    #renderer="checkmate:templates/admin/pages.html.jinja2",
    renderer="checkmate:templates/ui_app_dev.html.jinja2",
    effective_principals=[Principals.STAFF],
)
def admin_pages(_context, _request):
    """Render an HTML version of a blocked URL with explanation."""

    return {}


@view_config(route_name="admin_pages")
def admin_pages_logged_out(_context, request):
    return HTTPFound(location=request.route_url("login"))


@view_config(
    route_name="admin_login_failure",
    renderer="checkmate:templates/admin/login_failure.html.jinja2",
)
def admin_login_failure(_context, request):
    """Render a page when the user has failed to login."""

    request.response.status_code = 401  # Not authorized

    return {}
