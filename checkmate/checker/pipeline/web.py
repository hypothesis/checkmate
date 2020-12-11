"""Stages which deal with online sources."""

import requests
from requests import RequestException

from checkmate.checker.pipeline.core import Stage
from checkmate.exceptions import StageException


class Download(Stage):
    """A stage which downloads a URL and provides a file."""

    CHUNK_SIZE = 64000

    def __init__(self, url):
        self._url = url

    def __call__(self, working_dir, source=None):
        try:
            return self._download(self._url, working_dir)
        except RequestException as err:
            raise StageException(f"Could not download url {self._url}: {err}") from err

    @classmethod
    def _download(cls, url, working_dir):
        with requests.get(url, timeout=10) as response:
            response.raise_for_status()

            temp_file = cls.temp_file(working_dir, "zip")

            for chunk in response.iter_content(cls.CHUNK_SIZE):
                temp_file.write(chunk)

            return temp_file.name
