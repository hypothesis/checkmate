"""Application specific exceptions."""


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
