import os

import httpretty
import pytest
from httpretty import httprettified
from requests.exceptions import ReadTimeout

from checkmate.checker.pipeline import Download
from checkmate.exceptions import StageException


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

    def test_it_catches_requests_exceptions(self, tmpdir, requests):
        requests.get.side_effect = ReadTimeout
        url = "https://example.com"

        with pytest.raises(StageException):
            Download(url)(tmpdir)

        requests.get.assert_called_once_with(url, timeout=10)

    @pytest.fixture
    def requests(self, patch):
        return patch("checkmate.checker.pipeline.web.requests")
