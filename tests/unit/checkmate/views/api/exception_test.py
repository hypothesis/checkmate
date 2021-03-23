from pyramid.httpexceptions import HTTPForbidden

from checkmate.exceptions import JSONAPIException
from checkmate.views.api.exception import api_error, api_forbidden


class TestAPIError:
    def test_it(self, pyramid_request):
        error = JSONAPIException("message")
        error.status_code = 401

        response = api_error(error, pyramid_request)

        assert response == error.normalized_messages()
        assert pyramid_request.response.status_code == error.status_code


class TestAPIForbidden:
    def test_it(self, pyramid_request):
        response = api_forbidden(HTTPForbidden(), pyramid_request)

        assert pyramid_request.response.status_int == HTTPForbidden.code
        assert response == {"error": "invalid_token"}
