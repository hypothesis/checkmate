import os
from unittest import mock
from unittest.mock import Mock

import pyramid.config
import pytest

from checkmate.app import CheckmateConfigurator
from checkmate.authentication import APIHTTPAuth
from checkmate.models import Principals


class TestAPIAuth:
    @mock.patch.dict(os.environ, {})
    def test_load_keys_empty(self):
        config = pyramid.config.Configurator(settings={})
        CheckmateConfigurator._configure_api_keys(config)
        settings = config.get_settings()
        assert settings["api_keys"] == {}

    @mock.patch.dict(os.environ, {"CHECKMATE_API_KEY_USER_1": "api-key"})
    def test_load_keys(self):
        config = pyramid.config.Configurator(settings={})
        CheckmateConfigurator._configure_api_keys(config)
        settings = config.get_settings()

        assert settings["api_keys"] == {"api-key": "user_1"}

    def test_auth_callback_missing(self, pyramid_request):
        pyramid_request.registry.settings["api_keys"] = {}
        principals = APIHTTPAuth.check_callback("api_key", "password", pyramid_request)

        assert principals is None

    def test_auth_callback_existing(self, pyramid_request):
        pyramid_request.registry.settings["api_keys"] = {"api-key": "user_1"}
        principals = APIHTTPAuth.check_callback("api-key", "password", pyramid_request)

        assert principals == [Principals.API]

    def test_get_userid_no_credentials(
        self, extract_http_basic_credentials, auth, pyramid_request
    ):
        extract_http_basic_credentials.return_value = None
        userid = auth.unauthenticated_userid(pyramid_request)

        assert userid is None

    def test_get_userid_unknown_credentials(
        self, extract_http_basic_credentials, auth, pyramid_request
    ):
        extract_http_basic_credentials.return_value = None
        pyramid_request.registry.settings["api_keys"] = {}

        userid = auth.unauthenticated_userid(pyramid_request)

        assert userid is None

    def test_get_userid_credentials(
        self, extract_http_basic_credentials, auth, pyramid_request
    ):
        # HTTP auth username is the api key itself
        extract_http_basic_credentials.return_value = Mock(username="api-key")
        pyramid_request.registry.settings["api_keys"] = {"api-key": "user_1"}

        userid = auth.unauthenticated_userid(pyramid_request)

        assert userid == "user_1"

    @pytest.fixture
    def auth(self):
        return APIHTTPAuth()

    @pytest.fixture
    def extract_http_basic_credentials(self, patch):
        return patch("checkmate.authentication.extract_http_basic_credentials")
