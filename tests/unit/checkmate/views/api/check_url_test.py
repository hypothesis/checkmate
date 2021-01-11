import pytest

from checkmate.checker.url.reason import Reason
from checkmate.exceptions import BadURLParameter
from checkmate.url import hash_url
from checkmate.views.api.check_url import check_url


class TestURLCheck:
    def test_a_good_url(self, make_request, CustomRules, URLHaus):
        request = make_request("/api/check", {"url": "http://happy.example.com"})

        response = check_url(request)

        assert response.status_code == 204

        CustomRules.assert_called_once_with(request.db)
        custom_rules = CustomRules.return_value
        custom_rules.check_url.assert_called_once_with(
            list(hash_url("http://happy.example.com"))
        )

        URLHaus.assert_called_once_with(request.db)
        url_haus = CustomRules.return_value
        url_haus.check_url.assert_called_once_with(
            list(hash_url("http://happy.example.com"))
        )

    def test_a_bad_url(self, make_request, CustomRules, URLHaus):
        CustomRules.return_value.check_url.return_value = (Reason.MEDIA_IMAGE,)
        URLHaus.return_value.check_url.return_value = (Reason.MALICIOUS,)

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

    @pytest.fixture(autouse=True)
    def CustomRules(self, patch):
        CustomRules = patch("checkmate.views.api.check_url.CustomRules")
        CustomRules.return_value.check_url.return_value = tuple()
        return CustomRules

    @pytest.fixture(autouse=True)
    def URLHaus(self, patch):
        CustomRules = patch("checkmate.views.api.check_url.URLHaus")
        CustomRules.return_value.check_url.return_value = tuple()
        return CustomRules
