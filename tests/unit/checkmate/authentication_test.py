import pytest
from pyramid.authentication import HTTPBasicCredentials

from checkmate.auth import APIHTTPAuth
from checkmate.models import Principals


class TestAPIAuth:
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
        self, auth, extract_http_basic_credentials, pyramid_request
    ):
        # HTTP auth username is the api key itself
        credentials = HTTPBasicCredentials("api-key", None)
        extract_http_basic_credentials.return_value = credentials
        pyramid_request.registry.settings["api_keys"] = {"api-key": "user_1"}

        userid = auth.unauthenticated_userid(pyramid_request)

        assert userid == "user_1"

    @pytest.fixture
    def auth(self):
        return APIHTTPAuth()

    @pytest.fixture
    def extract_http_basic_credentials(self, patch):
        return patch("checkmate.auth.extract_http_basic_credentials")
