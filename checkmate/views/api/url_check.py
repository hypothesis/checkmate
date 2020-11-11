"""Monitoring views."""

from pyramid import response, view


@view.view_config(route_name="url_check")
def url_check(_request):
    """Status endpoint."""

    # If everything is fine give a 204 which is successful, but has no body
    return response.Response(status_int=204, status="204 OK")
