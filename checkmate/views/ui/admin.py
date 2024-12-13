from http.cookies import SimpleCookie

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import (
    forbidden_view_config,
    notfound_view_config,
    view_config,
    view_defaults,
)

from checkmate.exceptions import JSONAPIException
from checkmate.security import Permissions
from checkmate.services import RuleService


@view_config(route_name="admin.index")
def index(request):
    return HTTPFound(location=request.route_url("admin.allow_rule"))


@notfound_view_config(path_info="/admin/*", append_slash=True)
def notfound(_request):
    return HTTPNotFound()


@view_defaults(route_name="admin.pages", request_method="GET")
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
        return HTTPFound(location=self.request.route_url("pyramid_googleauth.login"))


@view_defaults(
    route_name="admin.allow_rule",
    permission=Permissions.ADMIN,
    renderer="checkmate:templates/admin/allow_rule.html.jinja2",
)
class AdminAllowViews:
    def __init__(self, request):
        self.request = request

    @view_config(request_method="GET")
    def get(self):
        return {}

    @view_config(request_method="POST")
    def post(self):
        url = self.request.params["url"]
        try:
            allow_rule = self.request.find_service(RuleService).add_to_allow_list(url)
        except JSONAPIException as e:
            return {"messages": e.messages}
        return {"allow_rule": allow_rule}
