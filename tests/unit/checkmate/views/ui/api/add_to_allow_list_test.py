import json

import pytest
from pyramid.httpexceptions import HTTPUnprocessableEntity

from checkmate.views.ui.api.add_to_allow_list import add_to_allow_list
from tests import factories

DELETE = ...


@pytest.mark.usefixtures("rule_service", "session")
class TestAddToAllowList:
    @pytest.mark.parametrize(
        "url", ("http://example.com", "//example.com", "example.com")
    )
    def test_it_handles_a_valid_request(self, pyramid_request, rule, url):
        self.set_json_body(pyramid_request, self.valid_body(url))

        response = add_to_allow_list(pyramid_request)

        assert response == {
            "data": {
                "id": rule.id,
                "type": "AllowRule",
                "attributes": {
                    "force": rule.force,
                    "hash": rule.hash,
                    "rule": rule.rule,
                    "tags": rule.tags,
                },
            }
        }

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
    def test_it_rejects_degenerate_submissions(self, pyramid_request, path, value):
        body = self.valid_body()
        self.set_path(body, path, value)
        self.set_json_body(pyramid_request, body)

        with pytest.raises(HTTPUnprocessableEntity):
            add_to_allow_list(pyramid_request)

    @classmethod
    def set_path(cls, data, path, value):
        target = data
        for path_item in path[:-1]:
            target = target[path_item]

        if value == DELETE:
            target.pop(path[-1])
        else:
            target[path[-1]] = value

    @classmethod
    def valid_body(cls, url="http://example.com"):
        return {"data": {"type": "AllowRule", "attributes": {"url": url}}}

    @classmethod
    def set_json_body(cls, request, body):
        request.body = json.dumps(body).encode("utf-8")
        request.content_type = "application/json"
        request.charset = "utf-8"

    @pytest.fixture
    def rule_service(self, rule_service, rule):
        rule_service.add_to_allow_list.return_value = rule

        return rule_service

    @pytest.fixture
    def rule(self):
        return factories.AllowRule.build(id=1234567)
