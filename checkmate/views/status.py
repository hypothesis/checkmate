from pyramid.view import view_config
from sentry_sdk import capture_message


@view_config(route_name="status", renderer="json", http_cache=0)
def status(request):
    if "sentry" in request.params:
        capture_message("Test message from Checkmate's status view")

    return {"status": "okay"}
