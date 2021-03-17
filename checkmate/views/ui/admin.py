from http.cookies import SimpleCookie

from pyramid.httpexceptions import HTTPFound
from pyramid.view import forbidden_view_config, view_config, view_defaults

from checkmate.security import Permissions


@view_defaults(route_name="admin_pages", request_method="GET")
class AdminPagesViews:
    def __init__(self, request):
        self.request = request

    @view_config(
        renderer="checkmate:templates/admin/pages.html.jinja2",
        permission=Permissions.ADMIN,
    )
    def get(self):
        cookie = SimpleCookie()
        cookie.load(self.request.headers["Cookie"])

        return {"session": cookie["session"].value}

    @forbidden_view_config()
    def logged_out(self):
        return HTTPFound(location=self.request.route_url("login"))


@view_config(
    route_name="admin_login_failure",
    renderer="checkmate:templates/admin/login_failure.html.jinja2",
)
def admin_login_failure(request):
    """Render a page when the user has failed to login."""

    request.response.status_code = 401  # Not authorized

    return {}
