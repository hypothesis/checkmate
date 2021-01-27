from unittest.mock import sentinel

from pyramid.httpexceptions import HTTPFound

from checkmate.views.ui.admin import (
    admin_login_failure,
    admin_pages,
    admin_pages_logged_out,
)


class TestAdminPages:
    def test_it(self, pyramid_request, session):
        response = admin_pages(sentinel.context, pyramid_request)

        assert response == {}


class TestAdminPagesLoggedOut:
    def test_it_redirects_to_login(self, pyramid_request):
        response = admin_pages_logged_out(sentinel.context, pyramid_request)

        assert isinstance(response, HTTPFound)
        assert response.location == "http://localhost/ui/api/login"


class TestAdminLoginFailure:
    def test_it_returns_unauthorized(self, pyramid_request):
        response = admin_login_failure(sentinel.context, pyramid_request)

        assert response == {}
        assert pyramid_request.response.status_code == 401
