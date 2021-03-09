from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPForbidden

from checkmate.views.ui.present_block import present_block


@pytest.mark.usefixtures("secure_link_service")
class TestPresentBlock:
    def test_it_passes_through_params(self, make_request, params):
        result = present_block(sentinel.context, make_request(params=params))

        assert result == {
            "blocked_url": params["url"],
            "reason": params["reason"],
            # Default values:
            "display_how_to_access": True,
            "annotated_with": "Via",
        }

    def test_passes_params_for_lms(self, make_request, params):
        params = dict(params)
        params["blocked_for"] = "lms"
        result = present_block(sentinel.context, make_request(params=params))

        assert result == {
            "blocked_url": params["url"],
            "reason": params["reason"],
            "display_how_to_access": False,
            "annotated_with": "Hypothesis",
        }

    def test_it_checks_param_signing(self, make_request, secure_link_service, params):
        secure_link_service.is_secure.return_value = False
        request = make_request(params=params)

        with pytest.raises(HTTPForbidden):
            present_block(sentinel.context, request)

        secure_link_service.is_secure.assert_called_once_with(request)

    @pytest.fixture
    def params(self):
        return {
            "url": "http://bad.example.com",
            "reason": "malicious",
            "v": "1",
            "sec": "some-long-token",
        }
