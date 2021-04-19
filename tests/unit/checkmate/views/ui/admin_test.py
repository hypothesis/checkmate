import pytest

from checkmate.views.ui.admin import AdminPagesViews
from tests.unit.matchers import temporary_redirect_to


class TestAdminPagesViews:
    def test_get(self, pyramid_request, views):
        pyramid_request.headers["Cookie"] = "session=session_value"

        response = views.get()

        assert response == {"session": "session_value"}

    def test_logged_out_redirects_to_login(self, pyramid_request, views):
        response = views.logged_out()

        assert response == temporary_redirect_to(
            pyramid_request.route_url("pyramid_googleauth.login")
        )

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminPagesViews(pyramid_request)
