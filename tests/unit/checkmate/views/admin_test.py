import pytest

from checkmate.exceptions import ResourceConflict
from checkmate.views.admin import AdminAllowRuleViews, index, notfound
from tests.unit.matchers import temporary_redirect_to


def test_admin_index(pyramid_request):
    response = index(pyramid_request)

    assert response == temporary_redirect_to(
        pyramid_request.route_url("admin.allow_url")
    )


def test_not_found_view(pyramid_request):
    response = notfound(pyramid_request)

    assert response.status_code == 404


class TestAdminAllowURLViews:
    def test_get(self, views):
        response = views.get()

        assert response == {}

    def test_post(self, pyramid_request, views, rule_service):
        pyramid_request.params["url"] = "http://example.com"

        response = views.post()

        rule_service.add_to_allow_list.assert_called_once_with(
            pyramid_request.params["url"]
        )
        assert response == {
            "allow_rule": rule_service.add_to_allow_list.return_value,
        }

    def test_post_empty_url(self, pyramid_request, views, rule_service):
        pyramid_request.params["url"] = ""

        response = views.post()

        rule_service.add_to_allow_list.assert_not_called()
        assert response == {"messages": [{"detail": "URL is required"}]}

    def test_post_with_conflict(self, pyramid_request, views, rule_service):
        pyramid_request.params["url"] = "http://example.com"
        exception = ResourceConflict("conflict")
        rule_service.add_to_allow_list.side_effect = exception

        response = views.post()

        rule_service.add_to_allow_list.assert_called_once_with(
            pyramid_request.params["url"]
        )
        assert response == {"messages": exception.messages}

    def test_logged_out_redirects_to_login(self, pyramid_request, views):
        response = views.logged_out()

        assert response == temporary_redirect_to(
            pyramid_request.route_url("pyramid_googleauth.login")
        )

    @pytest.fixture()
    def views(self, pyramid_request):
        return AdminAllowRuleViews(pyramid_request)
