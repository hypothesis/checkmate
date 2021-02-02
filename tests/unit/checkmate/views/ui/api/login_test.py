from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any
from pyramid.authentication import SessionAuthenticationPolicy

from checkmate.exceptions import UserNotAuthenticated
from checkmate.views.ui.api.login import login, login_callback, logout


@pytest.mark.usefixtures("google_auth_service")
class TestLogin:
    def test_it_redirects_to_google(self, pyramid_request, google_auth_service):
        response = login(sentinel.context, pyramid_request)

        google_auth_service.login_url.assert_called_once_with(
            force_login=True, login_hint=None
        )
        assert response.location == google_auth_service.login_url.return_value

    def test_it_allows_a_smooth_login_for_authenticated_users(
        self, pyramid_request, google_auth_service, auth_policy
    ):
        auth_policy.authenticated_userid.return_value = "staff@hypothes.is"

        login(sentinel.context, pyramid_request)

        google_auth_service.login_url.assert_called_once_with(
            force_login=False, login_hint="staff@hypothes.is"
        )

    def test_it_suggests_a_user_from_hint_parameter(
        self, pyramid_request, google_auth_service
    ):
        pyramid_request.GET["hint"] = "staff@hypothes.is"

        login(sentinel.context, pyramid_request)

        google_auth_service.login_url.assert_called_once_with(
            force_login=True, login_hint="staff@hypothes.is"
        )


@pytest.mark.usefixtures("google_auth_service", "session")
class TestLoginCallback:
    def test_it_sets_up_the_session(
        self, pyramid_request, google_auth_service, session, auth_policy
    ):
        session["some_noise"] = "which_should_be_cleared_out"
        user = {"email": "staff@hypothes.is", "user_other": "user_value"}

        google_auth_service.exchange_auth_code.return_value = user, sentinel.credentials

        response = login_callback(sentinel.context, pyramid_request)

        assert session == {"user": user}
        assert response.location == "http://localhost/ui/admin"
        auth_policy.remember.assert_called_once_with(
            pyramid_request, "staff@hypothes.is"
        )
        assert "Remember-Header" in list(response.headers)

    def test_it_bails_out_if_the_user_is_not_authenticated(
        self, pyramid_request, google_auth_service
    ):
        google_auth_service.exchange_auth_code.side_effect = UserNotAuthenticated

        response = login_callback(sentinel.context, pyramid_request)

        assert response.location == "http://localhost/ui/admin/login_failure"
        assert "Remember-Header" not in list(response.headers)


@pytest.mark.usefixtures("session", "auth_policy")
class TestLogout:
    def test_it_clears_the_session_and_redirects(self, pyramid_request, session):
        session["some_noise"] = "which_should_be_cleared_out"

        response = logout(sentinel.context, pyramid_request)

        assert session == {}
        assert response.location == "http://localhost/ui/api/login"
        assert "Forget-Header" in list(response.headers)

    def test_it_redirects_with_a_login_hint_if_possible(
        self, pyramid_request, auth_policy
    ):
        auth_policy.authenticated_userid.return_value = "staff@hypothes.is"

        response = logout(sentinel.context, pyramid_request)

        assert response.location == Any.url.containing_query(
            {"hint": "staff@hypothes.is"}
        )


@pytest.fixture
def auth_policy(pyramid_config):
    # This happens to be the policy we use, but we just need any concrete
    # one to make an auto spec from
    auth_policy = create_autospec(
        SessionAuthenticationPolicy, instance=True, spec_set=True
    )

    auth_policy.authenticated_userid.return_value = None
    auth_policy.remember.return_value = [("Remember-Header", "value")]
    auth_policy.forget.return_value = [("Forget-Header", "value")]

    # Pyramid requires something to be set for the authorization policy
    pyramid_config.set_authorization_policy(True)
    pyramid_config.set_authentication_policy(auth_policy)

    return auth_policy
