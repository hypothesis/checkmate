from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import (
    forbidden_view_config,
    notfound_view_config,
    view_config,
    view_defaults,
)

from checkmate.exceptions import ResourceConflict
from checkmate.security import Permissions
from checkmate.services import RuleService


@view_config(route_name="admin.index")
def index(request):
    return HTTPFound(location=request.route_url("admin.allow_url"))


@notfound_view_config(path_info="/admin/*", append_slash=True)
def notfound(_request):
    return HTTPNotFound()


@view_defaults(
    route_name="admin.allow_url",
    renderer="checkmate:templates/admin/allow_url.html.jinja2",
)
class AdminAllowRuleViews:
    def __init__(self, request):
        self.request = request

    @view_config(
        request_method="GET",
        permission=Permissions.ADMIN,
    )
    def get(self):
        return {}

    @view_config(
        request_method="POST",
        permission=Permissions.ADMIN,
    )
    def post(self):
        url = self.request.params.get("url")
        if not url:
            return {"messages": [{"detail": "URL is required"}]}
        try:
            allow_rule = self.request.find_service(RuleService).add_to_allow_list(url)
        except ResourceConflict as e:
            return {"messages": e.messages}
        return {"allow_rule": allow_rule}

    @forbidden_view_config()
    def logged_out(self):
        return HTTPFound(location=self.request.route_url("pyramid_googleauth.login"))
