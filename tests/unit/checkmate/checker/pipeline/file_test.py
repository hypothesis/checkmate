import os
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pkg_resources import resource_filename

from checkmate.checker.pipeline import ReadCSVFile, ReadTextFile, UnzipFile
from checkmate.exceptions import StageException


class TestReadTextFile:
    def test_it_reads_from_the_source(self, text_file):
        result = ReadTextFile()(sentinel.working_dir, source=text_file)

        assert result == Any.generator.containing(["line1\n", "line2"]).only()

    def test_it_reads_from_a_specified_name(self, text_file):
        result = ReadTextFile(text_file)(sentinel.working_dir)

        assert result == Any.generator.containing(["line1\n", "line2"]).only()

    def test_it_raises_if_not_given_a_file(self):
        with pytest.raises(StageException):
            list(ReadTextFile()(sentinel.working_dir, source=1234))

    @pytest.fixture
    def text_file(self, tmpdir):
        text_file = tmpdir / "a_file.txt"
        text_file.write("line1\nline2")

        return str(text_file)


class TestReadCSVFile:
    def test_it_reads_from_the_source(self, csv_file):
        result = ReadCSVFile()(sentinel.working_dir, source=csv_file)

        assert result == Any.generator.containing([["a", "b", "c"], ["1", "2", "3"]])

    def test_it_reads_from_a_specified_name(self, csv_file):
        result = ReadCSVFile(csv_file)(sentinel.working_dir)

        assert result == Any.generator.containing([["a", "b", "c"], ["1", "2", "3"]])

    def test_it_raises_if_not_given_a_file(self):
        with pytest.raises(StageException):
            list(ReadCSVFile()(sentinel.working_dir, source=1234))

    @pytest.fixture
    def csv_file(self, tmpdir):
        text_file = tmpdir / "a_file.txt"
        text_file.write("a,b,c\n# comment\n1,2,3\n")

        return str(text_file)


class TestUnzipFile:
    ZIP_FILE = resource_filename(__name__, "fixture.zip")

    def test_it_unzips_and_creates_a_file(self, tmpdir):
        result = UnzipFile("target.txt")(tmpdir, source=self.ZIP_FILE)

        assert os.path.isfile(result)

        with open(result) as handle:
            content = handle.read()

        assert content == "good"

    def test_it_raises_when_the_expected_file_is_missing(self, tmpdir):
        with pytest.raises(StageException):
            UnzipFile("missing.txt")(tmpdir, source=self.ZIP_FILE)

    def test_it_raises_for_bad_zips(self, tmpdir):
        not_a_zip = tmpdir / "not_a_zip.txt"
        not_a_zip.write("nope")

        with pytest.raises(StageException):
            UnzipFile("target.txt")(tmpdir, source=str(not_a_zip))

    def test_it_raises_if_not_given_a_file(self):
        with pytest.raises(StageException):
            UnzipFile("target.txt")(sentinel.working_dir, source=1234)
