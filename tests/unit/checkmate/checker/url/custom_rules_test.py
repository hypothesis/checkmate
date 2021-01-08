import pytest
from h_matchers import Any

from checkmate.checker.url.custom_rules import BlocklistParser, CustomRules
from checkmate.models import Reason
from checkmate.url import hash_url
from tests import factories


class TestCustomRules:
    @pytest.mark.parametrize("suffix", ("", "path", "path/nested", "with_query?a=b"))
    @pytest.mark.parametrize("prefix", ("http://", "https://subdomain."))
    def test_it_can_fuzzy_match_a_url(self, suffix, prefix, custom_rules):
        rule = factories.CustomRule()

        url = f"{prefix}{rule.rule}{suffix}"

        hits = custom_rules.check_url(hash_url(url))

        assert hits == Any.generator.containing(rule.reasons).only()

    def test_it_can_match_multiple_rules(self, custom_rules):
        factories.CustomRule(url="http://sub.domain.com", reasons=[Reason.HIGH_IO])
        factories.CustomRule(url="http://domain.com", reasons=[Reason.MALICIOUS])

        hits = custom_rules.check_url(hash_url("http://sub.domain.com"))

        assert (
            hits == Any.generator.containing([Reason.HIGH_IO, Reason.MALICIOUS]).only()
        )

    @pytest.fixture
    def custom_rules(self, db_session):
        return CustomRules(db_session)


class TestBlocklistParser:
    @pytest.mark.parametrize(
        "line,reason",
        (
            ("example.com publisher-blocked", Reason.PUBLISHER_BLOCKED),
            ("example.com malicious", Reason.MALICIOUS),
            ("   example.com    media-mixed   ", Reason.MEDIA_MIXED),
            (
                "example.com media-image   # trailing comment",
                Reason.MEDIA_IMAGE,
            ),
            ("example.com  media-video", Reason.MEDIA_VIDEO),
            ("example.com other", Reason.OTHER),
            ("example.com right-format-wrong-value", Reason.OTHER),
            # Comment
            ("# any old comment", None),
            # Unparsable
            ("example.com", None),
            ("example.com too many parts", None),
        ),
    )
    def test_line_parsing(self, tmp_path, line, reason):
        rules = BlocklistParser.parse_lines([line])

        if reason:
            assert list(rules) == [("example.com", reason)]
        else:
            assert not list(rules)
