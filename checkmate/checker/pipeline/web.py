"""Stages which deal with online sources."""

import requests
from requests.exceptions import ReadTimeout, RequestException

from checkmate.checker.pipeline.core import Stage
from checkmate.exceptions import StageException, StageTimeoutException


class Download(Stage):
    """A stage which downloads a URL and provides a file."""

    CHUNK_SIZE = 64000

    def __init__(self, url, timeout=10):
        """Initialise a stage to download a file.

        :param url: URL to retrieve
        :param timeout: Maximum time to wait on getting it
        :raise StageTimeoutException: If the request takes too long
        :raise StageException: For any other problems
        """
        self._url = url
        self._timeout = timeout

    def __call__(self, working_dir, source=None):
        try:
            return self._download(self._url, working_dir)
        except ReadTimeout as err:
            raise StageTimeoutException(
                f"Could not download url {self._url}: Timeout after {self._timeout}"
            ) from err
        except RequestException as err:
            raise StageException(f"Could not download url {self._url}: {err}") from err

    def _download(self, url, working_dir):
        with requests.get(url, timeout=self._timeout) as response:
            response.raise_for_status()

            temp_file = self.temp_file(working_dir, "zip")

            for chunk in response.iter_content(self.CHUNK_SIZE):
                temp_file.write(chunk)

            return temp_file.name
