import pytest
from marshmallow import ValidationError

from checkmate.views.derivers.jsonapi import JSONAPIBody
from checkmate.views.ui.api.add_to_allow_list import AllowRuleSchema, add_to_allow_list

DELETE = ...


class TestAllowRuleSchema:
    # These tests are probably over the top, but this is the first time we've
    # used marshmallow_jsonapi, so this is partly asserting that it works as
    # we would expect.

    @pytest.mark.parametrize(
        "path,value",
        (
            (["data"], DELETE),
            (["data", "type"], DELETE),
            (["data", "attributes"], DELETE),
            (["data", "attributes", "url"], DELETE),
            (["data", "attributes", "url"], "-completely <invalid> domain"),
            (["data", "attributes", "url"], "co.uk"),
            (["data", "attributes", "extras"], "not allowed"),
            # This doesn't seem to work...
            # As far as I can tell, marshmallow_jsonapi doesn't actually use
            # marshmallow validation to parse parts like "data" and
            # "attributes" out, it just plucks them out in pre-processing,
            # so there's no application of a schema in which we could add
            # "unknown=RAISE"
            # (["extras"], "not allowed"),
            # (["data", "extras"], "not allowed"),
        ),
    )
    def test_it_rejects_degenerate_submissions(self, path, value):
        body = self.valid_body()
        self.set_path(body, path, value)

        with pytest.raises(ValidationError):
            AllowRuleSchema().load(body)

    @pytest.mark.parametrize(
        "url", ("http://example.com", "//example.com", "example.com")
    )
    def test_it_accepts_a_valid_request(self, url):
        AllowRuleSchema().load(self.valid_body(url))

    @classmethod
    def valid_body(cls, url="http://example.com"):
        return {"data": {"type": "AllowRule", "attributes": {"url": url}}}

    @classmethod
    def set_path(cls, data, path, value):
        target = data
        for path_item in path[:-1]:
            target = target[path_item]

        if value == DELETE:
            target.pop(path[-1])
        else:
            target[path[-1]] = value


@pytest.mark.usefixtures("rule_service")
class TestAddToAllowList:
    def test_it(self, pyramid_request, rule_service):
        pyramid_request.jsonapi = JSONAPIBody(
            "AllowRule", {"url": "http://example.com"}
        )

        response = add_to_allow_list(pyramid_request)

        rule_service.add_to_allow_list.assert_called_once_with("http://example.com")
        assert response == rule_service.add_to_allow_list.return_value
