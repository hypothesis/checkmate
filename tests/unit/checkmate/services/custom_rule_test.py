from unittest.mock import sentinel

import pytest

from checkmate.models import Reason
from checkmate.services import CustomRuleService
from checkmate.services.custom_rule import factory


class TestCustomRuleService:
    def test_it_can_set_block_list(self, custom_rule_service):
        block_list = "example.com/ other"

        errors = custom_rule_service.set_block_list(block_list)

        assert errors == []
        assert custom_rule_service.get_block_list() == block_list

    def test_it_can_get_block_list(self, custom_rule_service):
        assert custom_rule_service.get_block_list() == ""

    def test_it_cannot_set_block_list_with_invalid_line(self, custom_rule_service):
        block_list = "example.com/other"

        errors = custom_rule_service.set_block_list(block_list)

        assert errors == [f"Cannot parse blocklist line: '{block_list}'"]

    def test_it_can_set_block_list_with_comments(self, custom_rule_service):
        block_list = "# comment.com/ other"

        errors = custom_rule_service.set_block_list(block_list)

        assert errors == []
        assert custom_rule_service.get_block_list() == ""

    def test_it_cannot_set_block_list_with_wildcard(self, custom_rule_service):
        block_list = "sub.*.example.com/ other"

        errors = custom_rule_service.set_block_list(block_list)

        assert errors == ["Cannot convert non prefix wildcard: 'sub.*.example.com/'"]

    def test_it_can_set_block_list_with_unknown_reason(self, custom_rule_service):
        block_list = "example.com/ unknown"

        errors = custom_rule_service.set_block_list(block_list)

        assert errors == []
        assert (
            custom_rule_service.get_block_list() == f"example.com/ {Reason.OTHER.value}"
        )

    def test_it_can_get_ordered_block_list(self, custom_rule_service):
        block_list = "example2.com/ other\nexample1.com/ malicious"

        custom_rule_service.set_block_list(block_list)

        lines = block_list.split("\n")
        assert custom_rule_service.get_block_list() == "\n".join(sorted(lines))

    @pytest.fixture
    def custom_rule_service(self, db_session):
        return CustomRuleService(db_session)


class TestFactory:
    def test_it(self, pyramid_request, CustomRuleService):
        result = factory(sentinel.context, pyramid_request)

        assert result == CustomRuleService.return_value
        CustomRuleService.assert_called_once_with(pyramid_request.db)

    @pytest.fixture
    def CustomRuleService(self, patch):
        return patch("checkmate.services.custom_rule.CustomRuleService")
