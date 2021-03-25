"""A view deriver which adds JSON:API processing to a view.

Any argument which is accepted by `JSONAPIViewWrapper` (aside from view) can be
passed in a view decorator by using the `jsonapi` argument. e.g.

    @view_config(
        request_method="POST",
        jsonapi={"schema": MyCustomSchema()},
    )
    def my_view(context, request):
        value = request.jsonapi.attributes['key']
        ...

Using this wrapper will:

 * Validate JSON:API spec requirements such as Accept and Content-Type
 * Parse a JSON:API body against the provided schema for POST and PATCH
 * Set the results of this parsing as `jsonapi` on the request object
   as a `JSONAPIBody` object
 * Wrap any return value and convert it into a valid JSON:API response
   using the provided schema
 * Format supported errors in JSON:API format

To exercise more control, you can return:

 * An model object which will be serialized using the provided schema
 * A dict which will be used as the body, but with JSON:API settings
 * A `JSONAPIResponse` object which will serialized using `make_response`
 * A pyramid request object which will be used verbatim
"""

from json import JSONDecodeError

from marshmallow import ValidationError
from pyramid.httpexceptions import (
    HTTPClientError,
    HTTPMethodNotAllowed,
    HTTPNotAcceptable,
    HTTPServerError,
    HTTPUnsupportedMediaType,
)
from pyramid.response import Response

from checkmate.exceptions import JSONAPIException, MalformedJSONBody

CONTENT_TYPE = "application/vnd.api+json"


class JSONAPIViewWrapper:
    """A view wrapper which adds JSON:API request and response processing."""

    def __init__(self, view, schema):
        """Initialise the wrapper.

        :param view: Pyramid view to wrap
        :param schema: `marshmallow_jsonapi.Schema` instance to validate
            requests and format responses
        """
        self._view = view
        self._schema = schema

    def __call__(self, context, request):
        """Call the wrapped view with JSON:API pre and post processing.

        :param context: Pyramid context
        :param request: Pyramid request

        :raises Exception: For any exception which cannot be converted to
            JSON:API format.
        """
        try:
            return self._handle_call(context, request)

        except Exception as exc:
            try:
                return JSONAPIResponse.from_exception(exc).make_response(
                    exc if isinstance(exc, Response) else request.response
                )
            except NotImplementedError:
                # An exception which we can't translate...
                pass

            # ... so we'll raise the original error
            raise

    def _handle_call(self, context, request):
        # Parse the request and make the result (if any) available to the
        # view as `jsonapi`
        request.jsonapi = JSONAPIRequest.parse(request, self._schema)

        # Default the status code to the ones used by JSON:API.
        # This is done before calling the view so the view can change the
        # status code if it wants to.
        request.response.status_code = JSONAPIResponse.DEFAULT_STATUS_CODES[
            request.method
        ]

        # Call the view
        view_result = self._view(context, request)

        # Looks like someone wants to return their own response... who are we
        # to judge? Allows for NoResponse and the like.
        if isinstance(view_result, Response):
            return view_result

        # Allow views to return `JSONAPIResponse` objects to support behavior
        # like returning results with different schema
        if not isinstance(view_result, JSONAPIResponse):
            view_result = JSONAPIResponse(view_result, schema=self._schema)

        # This is raw data which the view wants to be wrapped
        return view_result.make_response(request.response)


class JSONAPIRequest:
    """Logic for validating and processing JSON:API requests."""

    _SUPPORTED_METHODS = {"DELETE", "GET", "PATCH", "POST"}

    @classmethod
    def parse(cls, request, body_schema):
        """Parse a request applying JSON:API spec requirements.

        :param request: Pyramid request object
        :param body_schema: A schema to apply to the body (if any)
        :return: A `JSONAPIBody` for `POST` and `PATCH` or None
        """

        cls._check_accept(request)
        cls._check_content_type(request)
        cls._check_method(request)

        if request.method in {"POST", "PATCH"}:
            # Validate the JSON body using the schema
            return JSONAPIBody.from_request(request, body_schema)

        return None

    @classmethod
    def _check_accept(cls, request):
        # Servers MUST respond with a 406 Not Acceptable status code if a
        # request’s Accept header contains the JSON:API media type and all
        # instances of that media type are modified with media type parameters.

        if not request.accept:
            return

        media_types_counts = [
            len(parsed[2])
            for parsed in request.accept.parsed
            if parsed[0].startswith(CONTENT_TYPE)
        ]

        if not media_types_counts or 0 in media_types_counts:
            return

        raise HTTPNotAcceptable(
            f"If sent, Accept type '{CONTENT_TYPE}' "
            "must not contain media type parameters",
        )

    _SUPPORTED_CONTENT_TYPES = {
        "application/vnd.api+json",
        "application/json",
        # request.content_type is an empty string if the client sent no
        # Content-Type header.
        "",
    }

    @classmethod
    def _check_content_type(cls, request):
        # Servers MUST respond with a 415 Unsupported Media Type status code
        # if a request specifies the header Content-Type:
        # application/vnd.api+json with any media type parameters.

        if (
            request.content_type == CONTENT_TYPE
            and request.headers["Content-Type"] != CONTENT_TYPE
        ):
            raise HTTPUnsupportedMediaType(
                f"If sent, Content-Type type '{CONTENT_TYPE}' "
                "must not contain media type parameters",
            )

        # We'd also like to do some sanity checking
        if request.content_type not in cls._SUPPORTED_CONTENT_TYPES:
            raise HTTPUnsupportedMediaType(
                f"Unsupported Content-Type: {request.content_type}"
            )

    @classmethod
    def _check_method(cls, request):
        if request.method not in cls._SUPPORTED_METHODS:
            raise HTTPMethodNotAllowed(f"Method {request.method} not allowed")


class JSONAPIBody:
    """Data made available to the views about a JSON:API request."""

    def __init__(self, type_, attributes):
        """Initialise a body object.

        :param type_: The type of the JSON:API resource
        :param attributes: The attributes of the resource
        """
        self.type = type_
        self.attributes = attributes

    @staticmethod
    def from_request(request, schema):
        """Create a body object from a Pyramid request.

        :param request: Pyramid request to extract a body from
        :param schema: `marshmallow_jsonapi.Schema` to apply to the body

        :raise MalformedJSONBody: If the body is missing or invalid
        :raise ValidationError: If the body does not meet the schema
        """
        if not request.body:
            raise MalformedJSONBody("No JSON body found")

        try:
            data = request.json
        except JSONDecodeError as err:
            raise MalformedJSONBody(f"Could not parse JSON body: {err}") from err

        # Run the data through the schema before we attempt to access any part
        attributes = schema.load(data)

        return JSONAPIBody(type_=data["data"]["type"], attributes=attributes)


class JSONAPIResponse:
    """For emitting JSON:API responses from views.

    This is typically created for you by the view deriver, but you can return
    this directly from a view yourself if you want full control.
    """

    DEFAULT_STATUS_CODES = {
        "GET": 200,
        # A server MUST respond to a successful request to fetch an individual
        # resource or resource collection with a 200 OK response.
        "POST": 201,
        # If a POST request did not include a Client-Generated ID and the
        # requested resource has been created successfully, the server MUST
        # return a 201 Created status code.
        "PATCH": 200,
        # Updating things, JSON:API patch body expected
        "DELETE": 204
        # Delete obviously, no body
    }

    def __init__(self, data, schema=None, status_code=None):
        """Initialize the response.

        :param data: A dict to use as the response, or another object to pass
            through the provided schema to format the response
        :param schema: A `marshmallow_jsonapi.Schema` to apply to non dict
            objects
        :param status_code: Status code to set on the response
        """
        self.data = data
        self.schema = schema
        self.status_code = status_code

    @classmethod
    def from_exception(cls, exc):
        """Create a JSONAPIResponse from an exception.

        :param exc: Exception to convert
        :raise NotImplementedError: If the exception can't be converted
        """

        if isinstance(exc, ValidationError):
            # As long as these ValidationError's are from marshmallow_jsonapi
            # rather than plain Schema, it will have formatted the errors in
            # a JSON:API format for us. We have to assert this on the schema,
            # as the ValidationErrors are indistinguishable
            return cls(data=exc.normalized_messages(), status_code=400)

        if isinstance(exc, JSONAPIException):
            return cls(data=exc.normalized_messages(), status_code=exc.status_code)

        if isinstance(exc, (HTTPClientError, HTTPServerError)):
            return cls(
                data={"errors": [{"id": exc.__class__.__name__, "detail": exc.detail}]},
                status_code=exc.status_code,
            )

        # Don't know how to handle this one
        raise NotImplementedError(
            f"Unable to translate exception of type: {type(exc)}. "
            f"See SUPPORTED_ERROR_TYPES for a list of acceptable types"
        )

    def make_response(self, response):
        """Add JSON:API content type and body to a Pyramid request.

        This will also:

         * Ensure the Location and `self.links` match if present

        :param response: Pyramid request object to convert
        """
        if self.status_code:
            response.status_code = self.status_code

        body = self._serialize()
        self._set_self_location(response, body)

        response.json = body

        # Servers MUST send all JSON:API data in response documents with the
        # header Content-Type: application/vnd.api+json without any media
        # type parameters.
        response.content_type = CONTENT_TYPE

        return response

    def _serialize(self):
        if isinstance(self.data, dict):
            return self.data

        if self.schema:
            return self.schema.dump(self.data)

        raise ValueError(
            "You must either set an object to be serialized with a "
            "schema, or provide a raw data structure"
        )

    @classmethod
    def _set_self_location(cls, response, body):
        # The response SHOULD include a Location header identifying the
        # location of the newly created resource.

        # If the resource object returned by the response contains a self
        # key in its links member and a Location header is provided,
        # the value of the self member MUST match the value of the
        # Location header.

        location_header = response.headers.get("Location")
        try:
            link_self = body["links"]["self"]
        except KeyError:
            link_self = None

        if location_header and link_self and location_header != link_self:
            raise ValueError(
                "The location header and links.self must match if both are present"
            )

        if location_header and not link_self:
            body.setdefault("links", {})["self"] = location_header

        if link_self and not location_header:
            response.headers["Location"] = link_self


def jsonapi_view_deriver(view, info):
    """Wrap the view if required with a JSON:API conversion layer."""

    options = info.options.get("jsonapi")
    if options:
        return JSONAPIViewWrapper(view, **options)

    return view


# Tell Pyramid to allow the options as a @view_config() argument.
# (Pyramid throws an error if a @view_config() receives an unknown argument).
jsonapi_view_deriver.options = ["jsonapi"]
