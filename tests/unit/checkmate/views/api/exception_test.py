from unittest.mock import create_autospec

import pytest

from checkmate.exceptions import JSONAPIException
from checkmate.views.api.exception import api_error


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
