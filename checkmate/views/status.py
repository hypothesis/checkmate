"""The status end-point required to allow us to work with AWS."""

from pyramid.view import view_config


@view_config(route_name="get_status", renderer="json", http_cache=0)
def get_status(_request):
    """Status endpoint."""

    return {"status": "okay"}
