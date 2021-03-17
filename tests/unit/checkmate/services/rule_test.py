from unittest.mock import sentinel

import pytest
from h_matchers import Any

from checkmate.exceptions import ResourceConflict
from checkmate.models import AllowRule, Detection, Reason, Source
from checkmate.services import RuleService
from checkmate.services.rule import factory


class TestRuleService:
    def test_it_can_add_a_rule(self, rule_service, url_checker_service):
        url_checker_service.check_url.return_value = [
            Detection(Reason.NOT_ALLOWED, Source.ALLOW_LIST)
        ]

        rule = rule_service.add_to_allow_list("http://example.com")

        url_checker_service.check_url.assert_called_once_with(
            "http://example.com", fail_fast=False
        )
        assert rule == Any.instance_of(AllowRule).with_attrs(
            {
                "hash": Any.string(),
                "rule": "example.com/",
                "force": False,
                "tags": ["manual"],
            }
        )

    @pytest.mark.parametrize(
        "detections",
        (
            [],
            [
                Detection(Reason.NOT_ALLOWED, Source.ALLOW_LIST),
                Detection(Reason.MALICIOUS, Source.BLOCK_LIST),
            ],
        ),
    )
    def test_it_rejects_blocked_or_allowed_things(
        self, rule_service, url_checker_service, detections
    ):
        url_checker_service.check_url.return_value = detections

        with pytest.raises(ResourceConflict):
            rule_service.add_to_allow_list("http://example.com")

    @pytest.fixture
    def rule_service(self, url_checker_service, db_session):
        return RuleService(url_checker_service, db_session)


class TestFactory:
    def test_it(self, pyramid_request, RuleService, url_checker_service):
        result = factory(sentinel.context, pyramid_request)

        assert result == RuleService.return_value
        RuleService.assert_called_once_with(url_checker_service, pyramid_request.db)

    @pytest.fixture
    def RuleService(self, patch):
        return patch("checkmate.services.rule.RuleService")
