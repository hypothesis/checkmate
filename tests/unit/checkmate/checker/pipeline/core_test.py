import os
from unittest.mock import create_autospec, sentinel

import pytest

from checkmate.checker.pipeline.core import Pipeline, Stage
from checkmate.exceptions import StageException


class TestStage:
    def test_call_must_be_overriden(self):
        with pytest.raises(NotImplementedError):
            Stage()(working_dir="example")

    def test_temp_file(self, tmpdir):
        temp_file = Stage.temp_file(tmpdir, suffix=".suffix")

        assert temp_file.name.startswith(str(tmpdir))
        assert temp_file.name.endswith(".suffix")
        temp_file.write(b"content")  # Writable!

        # Persists on close
        temp_file.close()
        assert os.path.exists(temp_file.name)

        # Has the content
        with open(temp_file.name, encoding="utf8") as handle:
            content = handle.read()

        assert content == "content"

    def test_check_file_ok(self, tmpdir):
        filename = tmpdir / "a_file.txt"
        filename.write("content")

        Stage.check_file(str(filename))  # Ok!

    @pytest.mark.parametrize("not_a_file", [1234, "/tmp/not_a_valid_file"])
    def test_check_file_failures(self, not_a_file):
        with pytest.raises(StageException):
            Stage.check_file(not_a_file)


class TestPipeline:
    def test_it(self):
        stage_1 = create_autospec(Stage, instance=True, spec_set=True)
        stage_2 = create_autospec(Stage, instance=True, spec_set=True)

        pipeline = Pipeline([stage_1, stage_2])

        result = pipeline(
            working_dir=sentinel.working_dir, source=sentinel.initial_source
        )

        stage_1.assert_called_once_with(sentinel.working_dir, sentinel.initial_source)
        stage_2.assert_called_once_with(sentinel.working_dir, stage_1.return_value)
        assert result == stage_2.return_value
