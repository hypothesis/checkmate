from unittest.mock import sentinel

import pytest
from h_matchers import Any
from jwt.exceptions import JWTDecodeError
from oauthlib.oauth2.rfc6749.errors import InvalidClientError, InvalidGrantError

from checkmate.exceptions import BadOAuth2Config, UserNotAuthenticated
from checkmate.services.google_auth import GoogleAuthService, factory

# We do this all the time here, but it's ok for the tests of a file to poke
# about in the innards of that file
# pylint: disable=protected-access


class TestGoogleAuthService:
    @pytest.mark.parametrize(
        "redirect_uri,insecure",
        (("http://example.com", True), ("https://example.com", False)),
    )
    def test_it_allows_non_https_redirect_uris_for_dev(
        self, redirect_uri, client_config, insecure, os
    ):
        os.environ = {}
        client_config["redirect_uri"] = redirect_uri

        GoogleAuthService(sentinel.signature_service, client_config=client_config)

        assert bool(os.environ.get("OAUTHLIB_INSECURE_TRANSPORT")) == insecure

    def test_getting_a_flow(self, service, client_config, flow, Flow):
        # We aren't interested in login_url, but it triggers the call
        service.login_url()

        Flow.from_client_config.assert_called_once_with(
            {
                "web": {
                    "client_id": client_config["client_id"],
                    "client_secret": client_config["client_secret"],
                    "auth_uri": service.OPEN_ID_DISCOVERY["authorization_endpoint"],
                    "token_uri": service.OPEN_ID_DISCOVERY["token_endpoint"],
                }
            },
            scopes=service.SCOPES,
        )

        assert flow.redirect_uri == client_config["redirect_uri"]

    def test_getting_a_flow_raises_with_bad_config(self, service, Flow):
        # The google library raises a very vague error when this happens
        Flow.from_client_config.side_effect = ValueError

        with pytest.raises(BadOAuth2Config):
            # We aren't interested in login_url, but it triggers the call
            service.login_url()

    def test_login_url_base_case(self, service, flow):
        url = service.login_url()

        flow.authorization_url.assert_called_once_with(
            access_type="offline",
            include_granted_scopes="true",
            login_hint=Any(),
            state=service._signature_service.get_nonce.return_value,
            prompt=Any(),
        )

        authorization_url, state = flow.authorization_url.return_value

        assert url == authorization_url
        service._signature_service.check_nonce.assert_called_once_with(state)

    @pytest.mark.parametrize("login_hint", (None, "staff@hypothes.is"))
    @pytest.mark.parametrize("force_login", (True, False))
    def test_login_url_variations(self, service, flow, login_hint, force_login):
        service.login_url(login_hint, force_login)

        flow.authorization_url.assert_called_once_with(
            access_type=Any(),
            include_granted_scopes=Any(),
            login_hint=login_hint,
            state=Any(),
            prompt="select_account" if force_login else None,
        )

    def test_login_url_verifies_the_state(self, service, flow):
        service._signature_service.check_nonce.return_value = False

        with pytest.raises(UserNotAuthenticated):
            service.login_url()

    def test_exchange_auth_code_works(self, service, flow, JWT):
        redirect_url = "http://example.com?state=state_value"

        user_details, credentials = service.exchange_auth_code(redirect_url)

        flow.fetch_token.assert_called_once_with(authorization_response=redirect_url)
        JWT.return_value.decode.assert_called_once_with(
            flow.credentials.id_token, do_verify=False
        )

        # We extract and check the state/nonce
        service._signature_service.check_nonce.assert_called_once_with("state_value")

        assert user_details == JWT.return_value.decode.return_value
        assert credentials == {
            "token": flow.credentials.token,
            "refresh_token": flow.credentials.refresh_token,
            "id_token": flow.credentials.id_token,
            "token_uri": flow.credentials.token_uri,
            "client_id": flow.credentials.client_id,
            "client_secret": flow.credentials.client_secret,
            "scopes": flow.credentials.scopes,
        }

    def test_exchange_auth_code_checks_for_returned_errors(self, service, flow):
        with pytest.raises(UserNotAuthenticated):
            service.exchange_auth_code("http://example.com?error=oh_dear")

    def test_exchange_auth_code_checks_the_state(self, service):
        service._signature_service.check_nonce.return_value = False
        with pytest.raises(UserNotAuthenticated):
            service.exchange_auth_code("http://example.com?state=BAD_STATE")

    def test_exchange_auth_code_raises_if_user_not_authed(self, service, flow):
        flow.fetch_token.side_effect = InvalidGrantError

        with pytest.raises(UserNotAuthenticated):
            service.exchange_auth_code("http://example.com?state=state_value")

    def test_exchange_auth_code_raises_if_oauth_values_bad(self, service, flow):
        flow.fetch_token.side_effect = InvalidClientError

        with pytest.raises(BadOAuth2Config):
            service.exchange_auth_code("http://example.com?state=state_value")

    def test_exchange_auth_code_raises_with_a_bad_jwt(self, service, JWT):
        JWT.return_value.decode.side_effect = JWTDecodeError

        with pytest.raises(UserNotAuthenticated):
            service.exchange_auth_code("http://example.com?state=state_value")

    @pytest.fixture
    def client_config(self):
        return {
            "client_id": sentinel.client_id,
            "client_secret": sentinel.client_secret,
            "redirect_uri": "http://example.com",
        }

    @pytest.fixture
    def service(self, signature_service, client_config):
        return GoogleAuthService(signature_service, client_config)

    @pytest.fixture
    def flow(self, Flow):
        flow = Flow.from_client_config.return_value
        flow.authorization_url.return_value = sentinel.authorization_url, sentinel.state

        return flow

    @pytest.fixture(autouse=True)
    def os(self, patch):
        return patch("checkmate.services.google_auth.os")

    @pytest.fixture(autouse=True)
    def JWT(self, patch):
        return patch("checkmate.services.google_auth.JWT")

    @pytest.fixture(autouse=True)
    def Flow(self, patch):
        return patch("checkmate.services.google_auth.Flow")


class TestFactory:
    def test_it(self, pyramid_request, signature_service):
        pyramid_request.registry.settings = {
            "google_client_id": sentinel.google_client_id,
            "google_client_secret": sentinel.google_client_secret,
        }

        result = factory(sentinel.context, pyramid_request)

        assert result._signature_service == signature_service
        assert result._client_id == sentinel.google_client_id
        assert result._client_secret == sentinel.google_client_secret
        assert result._redirect_uri == "http://localhost/ui/api/login_callback"
