import pytest

from checkmate.views.ui.admin import (
    AdminAllowRuleViews,
    AdminPagesViews,
    index,
    notfound,
)
from tests.unit.matchers import temporary_redirect_to


def test_admin_index(pyramid_request):
    response = index(pyramid_request)

    assert response == temporary_redirect_to(
        pyramid_request.route_url("admin.allow_rule")
    )


def test_not_found_view(pyramid_request):
    response = notfound(pyramid_request)

    assert response.status_code == 404


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


class TestAdminAllowRuleViews:
    def test_get(self, views):
        response = views.get()

        assert response == {}

    def test_post(self, pyramid_request, views, rule_service):
        pyramid_request.params["url"] = "http://example.com"

        response = views.post()

        rule_service.add_to_allow_list.assert_called_once_with("http://example.com")
        assert response == {
            "allow_rule": rule_service.add_to_allow_list.return_value,
        }

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminAllowRuleViews(pyramid_request)
