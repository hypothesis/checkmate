import os
from unittest.mock import sentinel

import httpretty
import pytest
from httpretty import httprettified
from requests.exceptions import HTTPError, ReadTimeout

from checkmate.checker.pipeline import Download
from checkmate.exceptions import StageException, StageRetryableException


class TestDownload:
    @httprettified
    def test_it_downloads_a_file(self, tmpdir):
        url = "https://example.com"
        httpretty.register_uri(httpretty.GET, url, body="some content")

        result = Download(url)(tmpdir)

        assert os.path.isfile(result)
        with open(result) as handle:
            content = handle.read()

        assert content == "some content"

    @pytest.mark.parametrize(
        "exception,expected",
        (
            (HTTPError, StageException),
            (ReadTimeout, StageRetryableException),
        ),
    )
    def test_it_catches_requests_exceptions(
        self, tmpdir, requests, exception, expected
    ):
        requests.get.side_effect = exception
        url = "https://example.com"

        with pytest.raises(expected):
            Download(url)(tmpdir)

        requests.get.assert_called_once_with(url, timeout=10)

    def test_it_uses_the_timeout_value(self, tmpdir, requests):
        Download(sentinel.url, timeout=sentinel.timeout)(tmpdir)

        requests.get.assert_called_once_with(sentinel.url, timeout=sentinel.timeout)

    @pytest.fixture
    def requests(self, patch):
        return patch("checkmate.checker.pipeline.web.requests")
