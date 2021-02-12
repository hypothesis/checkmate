from unittest.mock import create_autospec

import pytest
from pyramid.httpexceptions import HTTPForbidden

from checkmate.exceptions import JSONAPIException
from checkmate.views.api.exception import api_error, api_forbidden


class TestAPIError:
    def test_it(self, pyramid_request, error):
        response = api_error(error, pyramid_request)

        assert response == {"errors": [error.serialise.return_value]}
        assert pyramid_request.response.status_code == error.status_code

    @pytest.fixture
    def error(self):
        error = create_autospec(JSONAPIException, spec_set=True, instance=True)
        error.status_code = 401
        return error


class TestAPIForbidden:
    def test_it(self, pyramid_request):
        response = api_forbidden(HTTPForbidden(), pyramid_request)

        assert pyramid_request.response.status_int == HTTPForbidden.code
        assert response == {"error": "invalid_token"}
