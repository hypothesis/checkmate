from unittest.mock import create_autospec

import pytest

from checkmate.checker.url.blocklist import Blocklist
from checkmate.checker.url.reason import Reason
from checkmate.exceptions import BadURLParameter, MalformedURL
from checkmate.views.api.check_url import check_url


class TestURLCheck:
    def test_a_good_url(self, make_request):
        request = make_request("/api/check", {"url": "http://happy.example.com"})

        result = check_url(request)

        assert result.status_code == 204

    def test_a_bad_url(self, make_request, blocklist):
        blocklist.check_url.return_value = (Reason.MEDIA_IMAGE, Reason.MALICIOUS)
        request = make_request("/api/check", {"url": "http://sad.example.com"})

        result = check_url(request)

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
        request = make_request("/api/check")

        with pytest.raises(BadURLParameter):
            check_url(request)

    def test_it_returns_an_error_if_blocklist_raises_MalformedURL(
        self, make_request, blocklist
    ):
        request = make_request("/api/check?url=http://")
        blocklist.check_url.side_effect = MalformedURL("URL is bad")

        with pytest.raises(BadURLParameter):
            check_url(request)

    @pytest.fixture
    def blocklist(self):
        blocklist = create_autospec(Blocklist, spec_set=True, instance=True)
        blocklist.check_url.return_value = tuple()
        return blocklist

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config, blocklist):
        pyramid_config.registry.url_blocklist = blocklist

        return pyramid_config
