from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config


@view_config(route_name="root")
def root(_context, request):
    return HTTPFound(location=request.route_url("login"))
