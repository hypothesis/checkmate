"""API exception views."""

from pyramid.view import exception_view_config, forbidden_view_config

from checkmate.exceptions import JSONAPIException


@exception_view_config(JSONAPIException, renderer="json")
def api_error(exc, request):
    """Handle JSON API compatible exceptions."""
    request.response.status_code = exc.status_code

    return {"errors": [exc.serialise()]}


@forbidden_view_config(path_info="^/api/.*$", renderer="json")
def api_forbidden(context, request):
    request.response.status_int = context.status_int
    return {"error": "invalid_token"}
