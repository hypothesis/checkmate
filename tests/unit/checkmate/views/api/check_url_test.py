from unittest.mock import create_autospec, sentinel

import pytest

from checkmate.checker.url.blocklist import Blocklist
from checkmate.checker.url.reason import Reason
from checkmate.exceptions import BadURLParameter, MalformedURL
from checkmate.url import hash_url
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

    def test_it_includes_results_from_custom_rules(self, make_request, CustomRules):
        request = make_request("/api/check?url=http://example.com")
        # This is going to need a rethink once this isn't optional any more
        request.db = sentinel.db_session

        CustomRules.return_value.check_url.return_value = (Reason.PUBLISHER_BLOCKED,)

        results = check_url(request)

        CustomRules.assert_called_once_with(request.db)
        custom_rules = CustomRules.return_value
        custom_rules.check_url.assert_called_once_with(
            list(hash_url("http://example.com"))
        )

        assert results["data"][0]["id"] == Reason.PUBLISHER_BLOCKED.value

    @pytest.fixture
    def blocklist(self):
        blocklist = create_autospec(Blocklist, spec_set=True, instance=True)
        blocklist.check_url.return_value = tuple()
        return blocklist

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config, blocklist):
        pyramid_config.registry.url_blocklist = blocklist

        return pyramid_config

    @pytest.fixture(autouse=True)
    def CustomRules(self, patch):
        return patch("checkmate.views.api.check_url.CustomRules")
