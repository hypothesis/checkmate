from unittest.mock import create_autospec

import pytest

from checkmate.checker.url.blocklist import Blocklist
from checkmate.checker.url.reason import Reason
from checkmate.exceptions import BadURLParameter
from checkmate.views.api.url_check import url_check


class TestURLCheck:
    def test_a_good_url(self, make_request):
        request = make_request("/api/url", {"url": "http://happy.example.com"})

        result = url_check(request)

        assert result.status_code == 204

    def test_a_bad_url(self, make_request, blocklist):
        blocklist.check_url.return_value = (Reason.MEDIA_IMAGE, Reason.MALICIOUS)
        request = make_request("/api/url", {"url": "http://sad.example.com"})

        result = url_check(request)

        assert request.response.status_code == 200
        assert result == {
            "data": [
                Reason.MALICIOUS.serialise(),
                Reason.MEDIA_IMAGE.serialise(),
            ],
            "meta": {
                "maxSeverity": "mandatory",
            },
        }

    def test_it_returns_an_error_for_no_url(self, make_request):
        request = make_request("/api/url")

        with pytest.raises(BadURLParameter):
            url_check(request)

    @pytest.fixture
    def blocklist(self):
        blocklist = create_autospec(Blocklist, spec_set=True, instance=True)
        blocklist.check_url.return_value = tuple()
        return blocklist

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config, blocklist):
        pyramid_config.registry.url_blocklist = blocklist

        return pyramid_config
