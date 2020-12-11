"""The core stage and pipeline objects."""

import os.path
from tempfile import NamedTemporaryFile

from checkmate.exceptions import StageException


class Stage:
    """A single stage which accepts a source and transforms it."""

    def __call__(self, working_dir, source=None):
        """Transform a source into a new output for another stage or consumer.

        :param working_dir: The directory to work within
        :param source: The source to transform (or None if we are first)
        :return: A new source for the next stage.
        """
        raise NotImplementedError("Subclasses must implement __call__")

    @staticmethod
    def temp_file(working_dir, suffix=None):
        """Get a temporary file."""

        return NamedTemporaryFile(dir=working_dir, delete=False, suffix=suffix)

    @staticmethod
    def check_file(filename):
        """Check that a source is a valid file.

        For use in calls to make sure the source is the expected type.
        """

        if not isinstance(filename, str):
            raise StageException(f"Expected a filename, but found {type(filename)}")

        if not os.path.isfile(filename):
            raise StageException(f"Expected file {filename} is missing")


class Pipeline(Stage):
    """A collection of stages which run together."""

    def __init__(self, stages):
        self.stages = stages

    def __call__(self, working_dir, source=None):
        for stage in self.stages:
            source = stage(working_dir, source)

        return source
