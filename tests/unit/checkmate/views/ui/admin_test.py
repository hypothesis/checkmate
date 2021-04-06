import pytest
from pyramid.httpexceptions import HTTPFound

from checkmate.views.ui.admin import AdminPagesViews, admin_login_failure


class TestAdminPagesViews:
    def test_get(self, pyramid_request, views):
        pyramid_request.headers["Cookie"] = "session=session_value"

        response = views.get()

        assert response == {"session": "session_value"}

    def test_logged_out_redirects_to_login(self, views):
        response = views.logged_out()

        assert isinstance(response, HTTPFound)
        assert response.location == "http://example.com/ui/api/login"

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminPagesViews(pyramid_request)


class TestAdminLoginFailure:
    def test_it_returns_unauthorized(self, pyramid_request):
        response = admin_login_failure(pyramid_request)

        assert response == {}
        assert pyramid_request.response.status_code == 401
