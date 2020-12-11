"""Stages which read files."""

import csv
from logging import getLogger
from zipfile import BadZipFile, ZipFile

from checkmate.checker.pipeline.core import Stage
from checkmate.exceptions import StageException

LOG = getLogger(__name__)


class ReadTextFile(Stage):
    """A stage which reads a file and outputs a generator of lines."""

    def __init__(self, name=None):
        self._name = name

    def __call__(self, working_dir, source=None):
        if source is None:
            source = self._name

        self.check_file(source)

        with open(source) as handle:
            yield from handle


class ReadCSVFile(ReadTextFile):
    """A stage which reads a CSV file and outputs a generator of rows."""

    def __call__(self, working_dir, source=None):
        lines = super().__call__(working_dir, source)
        cleaned_lines = (line for line in lines if not line.startswith("#"))

        yield from csv.reader(cleaned_lines)


class UnzipFile(Stage):
    """A stage which reads a file from a ZIP file and outputs a new file."""

    def __init__(self, file_in_zip):
        self._file_in_zip = file_in_zip

    def __call__(self, working_dir, source=None):
        self.check_file(source)

        try:
            zip_file = ZipFile(source)
        except BadZipFile as err:
            raise StageException(f"Cannot parse zip file '{source}'") from err

        try:
            return self._extract_file(self._file_in_zip, zip_file, working_dir)
        except KeyError as err:
            raise StageException(
                f"Cannot find requested file '{self._file_in_zip}' in zip"
            ) from err

    @classmethod
    def _extract_file(cls, file_name, zip_file, working_dir):
        with zip_file.open(file_name, mode="r") as zipped_file:
            temp_file = cls.temp_file(working_dir)
            for line in zipped_file:
                temp_file.write(line)

            return temp_file.name
