"""Application specific exceptions."""

# It's ok for exception hierarchies to get quite lanky
# pylint: disable=too-many-ancestors

from pyramid.httpexceptions import HTTPServerError, HTTPUnauthorized


class JSONAPIException(Exception):
    """A base exception for JSON API compatible errors."""

    # https://jsonapi.org/format/#errors
    status_code = 500

    def __init__(self, message):
        self.message = message

        super().__init__(message)

    def serialise(self):
        """Serialise to a JSON API error resource object."""
        return {"id": self.__class__.__name__, "detail": self.message}


class BadURLParameter(JSONAPIException):
    """Exception for malformed or missing parameters."""

    status_code = 400

    def __init__(self, param, message):
        self.param = param
        super().__init__(message)

    def serialise(self):
        """Serialise to a JSON API error resource object."""

        data = super().serialise()
        data["source"] = {"parameter": self.param}

        return data


class MalformedURL(Exception):
    """The URL is malformed in some way."""


class StageException(Exception):
    """A stage within a checker pipeline failed."""


class StageRetryableException(StageException):
    """A stage within a checker pipeline failed temporarily."""


class BadOAuth2Config(HTTPServerError):
    """Something is wrong with the OAuth2 configuration of our app."""


class UserNotAuthenticated(HTTPUnauthorized):
    """A user has failed authentication."""

    # This is not the same as a service to service authentication failure
