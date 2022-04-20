"""Application specific exceptions."""

# pylint: disable=unused-import
from checkmatelib.exceptions import BadURL


class JSONAPIException(Exception):
    """A base exception for JSON API compatible errors."""

    # https://jsonapi.org/format/#errors
    status_code = 500

    def __init__(self, message):
        self._message = message

        super().__init__(message)

    @property
    def messages(self):
        return [{"id": self.__class__.__name__, "detail": self._message}]

    def normalized_messages(self):
        """Serialise to a JSON API error resource object."""

        return {"errors": self.messages}


class BadURLParameter(JSONAPIException):
    """Exception for malformed or missing parameters."""

    status_code = 400

    def __init__(self, param, message):
        self.param = param
        super().__init__(message)

    @property
    def messages(self):
        messages = super().messages
        messages[0]["source"] = {"parameter": self.param}

        return messages


class ResourceConflict(JSONAPIException):
    """The request cannot be completed as it conflicts with existing state."""

    status_code = 409


class MalformedJSONBody(JSONAPIException):
    """The JSON body is malformed in some way."""

    status_code = 400


class StageException(Exception):
    """A stage within a checker pipeline failed."""


class StageRetryableException(StageException):
    """A stage within a checker pipeline failed temporarily."""
