import pytest

from checkmate.exceptions import BadURLParameter
from checkmate.models import Reason
from checkmate.views.api.check_url import check_url


@pytest.mark.usefixtures("secure_link_service")
class TestURLCheck:
    @pytest.mark.parametrize("allow_all", ("1", None))
    def test_a_good_url(self, make_request, allow_all, CompoundRules):
        params = {"url": "http://happy.example.com"}
        if allow_all:
            params["allow_all"] = allow_all

        request = make_request("/api/check", params)

        response = check_url(request)

        assert response.status_code == 204

        CompoundRules.assert_called_once_with(request.db, allow_all=allow_all)
        custom_rules = CompoundRules.return_value
        custom_rules.check_url.assert_called_once_with("http://happy.example.com")

    def test_a_bad_url(self, make_request, CompoundRules, secure_link_service):
        CompoundRules.return_value.check_url.return_value = (
            Reason.MALICIOUS,
            Reason.MEDIA_IMAGE,
        )
        bad_url = "http://sad.example.com"

        request = make_request("/api/check", {"url": bad_url})

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
            "links": {"html": secure_link_service.route_url.return_value},
        }

        secure_link_service.route_url.assert_called_once_with(
            "present_block", _query={"url": bad_url, "reason": Reason.MALICIOUS.value}
        )

    def test_it_returns_an_error_for_no_url(self, make_request):
        request = make_request("/api/check")

        with pytest.raises(BadURLParameter):
            check_url(request)

    @pytest.fixture(autouse=True)
    def CompoundRules(self, patch):
        CompoundRules = patch("checkmate.views.api.check_url.CompoundRules")
        CompoundRules.return_value.check_url.return_value = tuple()
        return CompoundRules
