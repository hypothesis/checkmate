import pytest

from checkmate.exceptions import BadURL, BadURLParameter
from checkmate.models import BlockedFor, Detection, Reason, Source
from checkmate.views.api.check_url import check_url


@pytest.mark.usefixtures("secure_link_service", "url_checker_service")
class TestURLCheck:
    @pytest.mark.parametrize("allow_all", ("1", None))
    def test_a_good_url(self, pyramid_request, allow_all, url_checker_service):
        pyramid_request.params["url"] = "http://happy.example.com"
        if allow_all:
            pyramid_request.params["allow_all"] = allow_all

        response = check_url(pyramid_request)

        assert response.status_code == 204

        url_checker_service.check_url.assert_called_once_with(
            "http://happy.example.com",
            allow_all=allow_all,
            ignore_reasons=[],
        )

    def test_a_bad_url(
        self,
        pyramid_request,
        url_checker_service,
        secure_link_service,
        pyramid_settings,
    ):
        url_checker_service.check_url.return_value = (
            Detection(Reason.MALICIOUS, Source.URL_HAUS),
            Detection(Reason.MEDIA_IMAGE, Source.BLOCK_LIST),
            Detection(Reason.MEDIA_IMAGE, Source.BLOCK_LIST),
        )
        pyramid_request.params["url"] = "http://sad.example.com"

        result = check_url(pyramid_request)

        assert pyramid_request.response.status_code == 200
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
                "url": pyramid_request.params["url"],
                "reason": Reason.MALICIOUS.value,  # pylint: disable=no-member
                "blocked_for": BlockedFor.GENERAL.value,
            },
        )

    def test_a_bad_url_ignored_reasons(self, pyramid_request, url_checker_service):
        pyramid_request.params.update(
            {
                "url": "http://sad.example.com",
                "ignore_reasons": ",".join(
                    [
                        Reason.MALICIOUS.value,  # pylint:disable=no-member
                        Reason.MEDIA_IMAGE.value,  # pylint:disable=no-member
                    ]
                ),
            }
        )

        check_url(pyramid_request)

        url_checker_service.check_url.assert_called_once_with(
            pyramid_request.params["url"],
            allow_all=None,
            ignore_reasons={Reason.MEDIA_IMAGE, Reason.MALICIOUS},
        )

    def test_it_returns_an_error_for_no_url(self, pyramid_request):
        with pytest.raises(BadURLParameter):
            check_url(pyramid_request)

    def test_it_returns_an_error_for_unknown_ignore_reason(self, pyramid_request):
        pyramid_request.params.update(
            {"url": "example.com", "ignore_reasons": "whatever"}
        )

        with pytest.raises(BadURLParameter):
            check_url(pyramid_request)

    def test_it_returns_an_error_for_invalid_url(
        self, pyramid_request, url_checker_service
    ):
        pyramid_request.params["url"] = "http://example.com]"
        url_checker_service.check_url.side_effect = BadURL()

        with pytest.raises(BadURLParameter):
            check_url(pyramid_request)
