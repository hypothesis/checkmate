from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPUnauthorized

from checkmate.views.ui.present_block import present_block


@pytest.mark.usefixtures("secure_link_service")
class TestPresentBlock:
    def test_it_passes_through_params(self, pyramid_request):
        result = present_block(sentinel.context, pyramid_request)

        assert result == {
            "blocked_url": pyramid_request.params["url"],
            "reason": pyramid_request.params["reason"],
            # Default values:
            "display_how_to_access": True,
            "annotated_with": "Via",
        }

    def test_passes_params_for_lms(self, pyramid_request):
        pyramid_request.params["blocked_for"] = "lms"
        result = present_block(sentinel.context, pyramid_request)

        assert result == {
            "blocked_url": pyramid_request.params["url"],
            "reason": pyramid_request.params["reason"],
            "display_how_to_access": False,
            "annotated_with": "Hypothesis",
        }

    def test_it_checks_param_signing(self, pyramid_request, secure_link_service):
        secure_link_service.is_secure.return_value = False

        with pytest.raises(HTTPUnauthorized):
            present_block(sentinel.context, pyramid_request)

        secure_link_service.is_secure.assert_called_once_with(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params.update(
            {
                "url": "http://bad.example.com",
                "reason": "malicious",
                "v": "1",
                "sec": "some-long-token",
            }
        )
        return pyramid_request
