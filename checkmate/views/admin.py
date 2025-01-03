from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import (
    forbidden_view_config,
    notfound_view_config,
    view_config,
    view_defaults,
)

from checkmate.exceptions import ResourceConflict
from checkmate.security import Permissions
from checkmate.services import CustomRuleService, RuleService


@view_config(route_name="admin.index")
def index(request):
    return HTTPFound(location=request.route_url("admin.allow_url"))


@notfound_view_config(path_info="/admin/*", append_slash=True)
def notfound(_request):
    return HTTPNotFound()


@forbidden_view_config(path_info="/admin/*")
def logged_out(request):
    return HTTPFound(location=request.route_url("pyramid_googleauth.login"))


@view_defaults(
    route_name="admin.allow_url",
    renderer="checkmate:templates/admin/allow_url.html.jinja2",
    permission=Permissions.ADMIN,
)
class AdminAllowRuleViews:
    def __init__(self, request):
        self._request = request
        self._rule_service: RuleService = request.find_service(RuleService)

    @view_config(request_method="GET")
    def get(self):
        return {}

    @view_config(request_method="POST")
    def post(self):
        url = self._request.params.get("url")
        if not url:
            return {"messages": [{"detail": "URL is required"}]}
        try:
            allow_rule = self._rule_service.add_to_allow_list(url)
        except ResourceConflict as e:
            return {"messages": e.messages}
        return {"allow_rule": allow_rule}


@view_defaults(
    route_name="admin.block_list",
    renderer="checkmate:templates/admin/block_list.html.jinja2",
    permission=Permissions.ADMIN,
)
class AdminBlockListViews:
    def __init__(self, request):
        self._request = request
        self._custom_rule_service: CustomRuleService = request.find_service(
            CustomRuleService
        )

    @view_config(request_method="GET")
    def get(self):
        block_list = self._custom_rule_service.get_block_list()
        return {"block_list": block_list}

    @view_config(request_method="POST")
    def post(self):
        block_list: str = self._request.POST["block-list"]
        if not block_list:
            return {"errors": ["Block List is required"]}

        errors = self._custom_rule_service.set_block_list(block_list)
        if errors:
            return {"errors": errors, "block_list": block_list}

        block_list = self._custom_rule_service.get_block_list()
        return {"message": "Block List set successfully", "block_list": block_list}
