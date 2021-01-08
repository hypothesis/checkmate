import pytest
from h_matchers import Any

from checkmate.checker.url.allow_rules import AllowRules
from checkmate.models import Reason
from checkmate.url import hash_url
from tests import factories


class TestAllowRules:
    @pytest.mark.parametrize("suffix", ("", "path", "path/nested", "with_query?a=b"))
    @pytest.mark.parametrize("prefix", ("http://", "https://subdomain."))
    def test_it_can_fuzzy_allow_a_url(self, suffix, prefix, allow_rules):
        rule = factories.AllowRule()

        url = f"{prefix}{rule.rule}{suffix}"

        hits = allow_rules.check_url(hash_url(url))

        # When things match with the Allow list we get no reasons
        assert hits == Any.generator.of_size(0)

    def test_it_can_detect_a_missing_url(self, allow_rules):
        _noise = factories.AllowRule()

        hits = allow_rules.check_url(hash_url("http://not-a-match.com"))

        assert hits == Any.generator.containing([Reason.NOT_ALLOWED]).only()

    @pytest.fixture
    def allow_rules(self, db_session):
        return AllowRules(db_session)
