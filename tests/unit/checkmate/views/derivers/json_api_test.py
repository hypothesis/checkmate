import json
from unittest.mock import create_autospec, sentinel

import pytest
from marshmallow import ValidationError
from marshmallow.exceptions import SCHEMA
from marshmallow_jsonapi import Schema, fields
from pyramid.config.views import ViewDeriverInfo
from pyramid.httpexceptions import (
    HTTPCreated,
    HTTPFound,
    HTTPMethodNotAllowed,
    HTTPNotAcceptable,
    HTTPServerError,
    HTTPUnsupportedMediaType,
)
from pyramid.response import Response
from pytest import param

from checkmate.exceptions import MalformedJSONBody, ResourceConflict
from checkmate.views.derivers.json_api import (
    JSONAPIBody,
    JSONAPIRequest,
    JSONAPIResponse,
    JSONAPIViewWrapper,
    json_api_view_deriver,
)


class DummySchema(Schema):
    id = fields.Int()
    key = fields.Str(required=True)

    class Meta:
        type_ = "test_schema"


class TestJSONAPIBody:
    def test_it_parses_the_body(self, pyramid_request):
        pyramid_request.body = json.dumps(
            {"data": {"type": "test_schema", "attributes": {"key": "value"}}}
        ).encode("utf-8")

        body = JSONAPIBody.from_request(pyramid_request, DummySchema())

        assert body.attributes == {"key": "value"}
        assert body.type == "test_schema"

    def test_it_rejects_missing_bodies(self, pyramid_request):
        with pytest.raises(MalformedJSONBody):
            JSONAPIBody.from_request(pyramid_request, DummySchema())

    def test_it_rejects_malformed_bodies(self, pyramid_request):
        pyramid_request.body = b"<not json>"

        with pytest.raises(MalformedJSONBody):
            JSONAPIBody.from_request(pyramid_request, DummySchema())

    def test_it_rejects_valid_json_which_doesnt_match_the_schema(self, pyramid_request):
        pyramid_request.body = json.dumps({}).encode("utf-8")

        with pytest.raises(ValidationError):
            JSONAPIBody.from_request(pyramid_request, DummySchema())


class TestJSONAPIResponse:
    def test_it_sets_the_status_code(self, pyramid_request):
        JSONAPIResponse({}, status_code=209).make_response(pyramid_request.response)

        assert pyramid_request.response.status_code == 209

    def test_it_uses_dict_data_directly(self, pyramid_request):
        JSONAPIResponse({"custom": "data"}).make_response(pyramid_request.response)

        assert pyramid_request.response.json == {"custom": "data"}

    def test_it_uses_the_schema_for_other_objects(self, response):
        class TestObject:
            key = "value"

        JSONAPIResponse(TestObject(), DummySchema()).make_response(response)

        assert response.json == {
            "data": {"attributes": {"key": "value"}, "type": "test_schema"}
        }

    def test_it_raises_if_no_schema_is_present_for_non_dicts(self, response):
        class TestObject:
            ...

        with pytest.raises(ValueError):
            JSONAPIResponse(TestObject()).make_response(response)

    def test_it_sets_links_self_from_location(self, pyramid_request):
        pyramid_request.response.headers["Location"] = "http://example.com"

        JSONAPIResponse({}).make_response(pyramid_request.response)

        assert pyramid_request.response.json == {
            "links": {"self": "http://example.com"}
        }

    def test_it_sets_location_from_links_self(self, pyramid_request):
        data = {"links": {"self": "http://example.com"}}

        JSONAPIResponse(data).make_response(pyramid_request.response)

        assert pyramid_request.response.headers["Location"] == "http://example.com"

    def test_it_raises_if_location_and_self_links_are_different(self, pyramid_request):
        pyramid_request.response.headers["Location"] = "http://example.com"
        data = {"links": {"self": "http://DIFFERENT.example.com"}}

        with pytest.raises(ValueError):
            JSONAPIResponse(data).make_response(pyramid_request.response)

    def test_it_sets_the_content_type(self, response):
        JSONAPIResponse({}).make_response(response)

        assert response.content_type == "application/vnd.api+json"

    @pytest.mark.parametrize(
        "error,status_code,body",
        (
            param(
                HTTPNotAcceptable("message"),
                406,
                {"errors": [{"detail": "message", "id": "HTTPNotAcceptable"}]},
                id="pyramid_client_error",
            ),
            param(
                HTTPServerError("message"),
                500,
                {"errors": [{"detail": "message", "id": "HTTPServerError"}]},
                id="pyramid_server_error",
            ),
            param(
                ResourceConflict("message"),
                409,
                {"errors": [{"detail": "message", "id": "ResourceConflict"}]},
                id="json_api_error",
            ),
            param(
                ValidationError(field_name=SCHEMA, message="content-irrelevant"),
                400,
                # It's a marshmallow_jsonapi.Schema concern to format these errors
                # so the exact content here doesn't matter
                {"_schema": ["content-irrelevant"]},
                id="marshmallow_error",
            ),
        ),
    )
    def test_it_can_translate_supported_exceptions(
        self, response, error, status_code, body
    ):
        JSONAPIResponse.from_exception(error).make_response(response)

        assert response.status_code == status_code
        assert response.json == body

    @pytest.mark.parametrize("error", (HTTPFound, HTTPCreated, ValueError))
    def test_it_cannot_translate_unsupported_exceptions(self, error):
        with pytest.raises(NotImplementedError):
            JSONAPIResponse.from_exception(error())

    @pytest.fixture
    def response(self, pyramid_request):
        return pyramid_request.response


class TestJSONAPIRequest:
    @pytest.mark.parametrize(
        "accept_header",
        (
            # We don't have to actually care about the accept header according
            # to the spec
            "text/html",
            None,
            "application/json",
            # ... unless it's "application/vnd.api+json" with media queries
            (
                "application/vnd.api+json; this-is-ok=if-theres-a-normal-one-too,"
                "application/vnd.api+json"
            ),
        ),
    )
    def test_it_allows_valid_accepts(self, accept_header, pyramid_request):
        if accept_header:
            pyramid_request.environ["HTTP_ACCEPT"] = accept_header

        JSONAPIRequest.parse(pyramid_request, body_schema=None)

    def test_it_rejects_accept_with_media_queries(self, pyramid_request):
        pyramid_request.environ["HTTP_ACCEPT"] = (
            "application/vnd.api+json; this-is-bad=if-they-all-have-it, "
            "application/vnd.api+json; i-have-it=too"
        )

        with pytest.raises(HTTPNotAcceptable):
            JSONAPIRequest.parse(pyramid_request, body_schema=None)

    @pytest.mark.parametrize(
        "content_type",
        (
            "application/vnd.api+json",
            "application/json",
            "",
        ),
    )
    def test_it_allows_valid_content_types(self, pyramid_request, content_type):
        pyramid_request.content_type = content_type

        JSONAPIRequest.parse(pyramid_request, body_schema=None)

    @pytest.mark.parametrize(
        "content_type",
        (
            "text/html",
            "application/vnd.api+json; no-media-params=are-allowed",
        ),
    )
    def test_it_rejects_invalid_content_types(self, pyramid_request, content_type):
        pyramid_request.content_type = content_type

        with pytest.raises(HTTPUnsupportedMediaType):
            JSONAPIRequest.parse(pyramid_request, body_schema=None)

    @pytest.mark.parametrize("method", ("DELETE", "GET", "PATCH", "POST"))
    def test_it_allows_supported_methods(self, method, pyramid_request):
        pyramid_request.method = method

        JSONAPIRequest.parse(pyramid_request, body_schema=None)

    @pytest.mark.parametrize("method", ("PUT", "OPTIONS"))
    def test_it_rejects_unsupported_methods(self, method, pyramid_request):
        pyramid_request.method = method

        with pytest.raises(HTTPMethodNotAllowed):
            JSONAPIRequest.parse(pyramid_request, body_schema=None)

    @pytest.mark.parametrize("method", ("PATCH", "POST"))
    def test_it_parses_json_body_for_supported_methods(
        self, pyramid_request, JSONAPIBody, method
    ):
        pyramid_request.method = method

        response = JSONAPIRequest.parse(pyramid_request, body_schema=sentinel.schema)

        JSONAPIBody.from_request.assert_called_once_with(
            pyramid_request, sentinel.schema
        )
        assert response == JSONAPIBody.from_request.return_value

    @pytest.fixture(autouse=True)
    def JSONAPIBody(self, patch):
        return patch("checkmate.views.derivers.json_api.JSONAPIBody")


class TestJSONAPIViewWrapper:
    def test_it_calls_the_view_method(self, view, wrapper, pyramid_request):
        wrapper(sentinel.context, pyramid_request)

        view.assert_called_once_with(sentinel.context, pyramid_request)

    def test_it_requires_the_schema_to_be_a_jsonapi_schema(self, view):
        # We check specifically for `marshmallow_jsonapi` schema. A common
        # mistake might be to use regular marshmallow schema
        # pylint: disable=import-outside-toplevel
        from marshmallow import Schema as PlainSchema

        schema = PlainSchema()

        with pytest.raises(ValueError):
            JSONAPIViewWrapper(view, schema)

    @pytest.mark.parametrize(
        "method,status_code",
        (("GET", 200), ("POST", 201), ("PATCH", 200), ("DELETE", 204)),
    )
    def test_it_sets_the_default_status_code_based_on_method(
        self, wrapper, pyramid_request, method, status_code
    ):
        pyramid_request.method = method

        wrapper(sentinel.context, pyramid_request)

        assert pyramid_request.response.status_code == status_code

    def test_it_parses_the_request_and_makes_results_available_to_the_view(
        self, view, pyramid_request, JSONAPIRequest
    ):
        schema = DummySchema()
        wrapper = JSONAPIViewWrapper(view, schema)

        wrapper(sentinel.context, pyramid_request)

        JSONAPIRequest.parse.assert_called_once_with(pyramid_request, schema)
        assert pyramid_request.json_api == JSONAPIRequest.parse.return_value

    def test_it_transparently_passes_response_objects(self, view, wrapper_caller):
        view.return_value = Response()

        wrapped_response = wrapper_caller()

        assert wrapped_response is view.return_value

    def test_it_serialises_json_api_response_objects(
        self, view, wrapper_caller, pyramid_request
    ):
        class CustomResponse(JSONAPIResponse):
            def make_response(self, response):
                assert response == pyramid_request.response

                return "custom_response"

        json_api_response = CustomResponse({})
        view.return_value = json_api_response

        wrapped_response = wrapper_caller()

        assert wrapped_response == "custom_response"

    def test_it_wraps_and_serializes_other_objects(
        self, view, wrapper_caller, pyramid_request
    ):
        class TestObject:
            key = "value"

        view.return_value = TestObject()
        schema = DummySchema()
        wrapper = JSONAPIViewWrapper(view, schema)

        result = wrapper(sentinel.context, pyramid_request)

        assert result.json == {
            "data": {"attributes": {"key": "value"}, "type": "test_schema"}
        }

    def test_it_converts_pyramid_http_exceptions(self, wrapper_caller, JSONAPIRequest):
        JSONAPIRequest.parse.side_effect = HTTPNotAcceptable("message")

        result = wrapper_caller()

        assert result.json == {
            "errors": [{"detail": "message", "id": "HTTPNotAcceptable"}]
        }

    def test_it_reraises_unwrappable_exceptions(self, wrapper_caller, JSONAPIRequest):
        JSONAPIRequest.parse.side_effect = ValueError("message")

        with pytest.raises(ValueError):
            wrapper_caller()

    @pytest.fixture
    def view(self):
        def view(context, request):  # pragma: no cover
            ...

        return create_autospec(view, spec_set=True)

    @pytest.fixture
    def wrapper(self, view):
        return JSONAPIViewWrapper(view, DummySchema())

    @pytest.fixture
    def wrapper_caller(self, wrapper, pyramid_request):
        def wrapper_caller():
            return wrapper(sentinel.context, pyramid_request)

        return wrapper_caller

    @pytest.fixture(autouse=True)
    def JSONAPIRequest(self, patch):
        return patch("checkmate.views.derivers.json_api.JSONAPIRequest")


class TestJSONAPIViewDeriver:
    def test_it_wraps_the_view_with_options(self, info, JSONAPIViewWrapper):
        info.options["json_api"] = {"schema": sentinel.schema}

        result = json_api_view_deriver(sentinel.view, info)

        JSONAPIViewWrapper.assert_called_once_with(
            sentinel.view, schema=sentinel.schema
        )

        assert result == JSONAPIViewWrapper.return_value

    def test_it_does_nothing_without_options(self, info):
        result = json_api_view_deriver(sentinel.view, info)

        assert result == sentinel.view

    @pytest.fixture
    def info(self):
        info = create_autospec(ViewDeriverInfo, instance=True)
        info.options = {}

        return info

    @pytest.fixture(autouse=True)
    def JSONAPIViewWrapper(self, patch):
        return patch("checkmate.views.derivers.json_api.JSONAPIViewWrapper")
