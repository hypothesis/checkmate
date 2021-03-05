import pytest

from checkmate.exceptions import BadURLParameter, MalformedURL
from checkmate.models import BlockedFor, Detection, Reason, Source
from checkmate.views.api.check_url import check_url


@pytest.mark.usefixtures("secure_link_service", "url_checker_service")
class TestURLCheck:
    @pytest.mark.parametrize("allow_all", ("1", None))
    def test_a_good_url(self, make_request, allow_all, url_checker_service):
        params = {"url": "http://happy.example.com"}
        if allow_all:
            params["allow_all"] = allow_all

        request = make_request("/api/check", params)

        response = check_url(request)

        assert response.status_code == 204

        url_checker_service.check_url.assert_called_once_with(
            "http://happy.example.com",
            allow_all=allow_all,
            ignore_reasons=[],
        )

    def test_a_bad_url(
        self, make_request, url_checker_service, secure_link_service, pyramid_settings
    ):
        url_checker_service.check_url.return_value = (
            Detection(Reason.MALICIOUS, Source.URL_HAUS),
            Detection(Reason.MEDIA_IMAGE, Source.BLOCK_LIST),
            Detection(Reason.MEDIA_IMAGE, Source.BLOCK_LIST),
        )
        bad_url = "http://sad.example.com"

        request = make_request("/api/check", {"url": bad_url})

        result = check_url(request)

        assert request.response.status_code == 200
        assert result == {
            # pylint: disable=no-member
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
            "present_block",
            _scheme=pyramid_settings["public_scheme"],
            _port=pyramid_settings["public_port"],
            _host=pyramid_settings["public_host"],
            _query={
                "url": bad_url,
                "reason": Reason.MALICIOUS.value,  # pylint: disable=no-member
                "blocked_for": BlockedFor.GENERAL.value,
            },
        )

    def test_a_bad_url_ignored_reasons(
        self, make_request, url_checker_service, secure_link_service, pyramid_settings
    ):
        bad_url = "http://sad.example.com"

        request = make_request(
            "/api/check",
            {
                "url": bad_url,
                "ignore_reasons": ",".join(
                    # pylint: disable=no-member
                    [
                        Reason.MALICIOUS.value,
                        Reason.MEDIA_IMAGE.value,
                    ]
                ),
            },
        )

        check_url(request)

        url_checker_service.check_url.assert_called_once_with(
            "http://sad.example.com",
            allow_all=None,
            ignore_reasons=set([Reason.MEDIA_IMAGE, Reason.MALICIOUS]),
        )

    def test_it_returns_an_error_for_no_url(self, make_request):
        request = make_request("/api/check")

        with pytest.raises(BadURLParameter):
            check_url(request)

    def test_it_returns_an_error_for_unknown_ignore_reason(self, make_request):
        request = make_request(
            "/api/check", {"url": "example.com", "ignore_reasons": "whatever"}
        )

        with pytest.raises(BadURLParameter):
            check_url(request)

    def test_it_returns_an_error_for_invalid_url(
        self, make_request, url_checker_service
    ):
        request = make_request("/api/check", {"url": "http://example.com]"})

        url_checker_service.check_url.side_effect = MalformedURL()

        with pytest.raises(BadURLParameter):
            check_url(request)
