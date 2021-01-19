from collections import namedtuple

import pytest
from pytest import param

from checkmate.url.domain._domain_core import DomainCore
from checkmate.url.domain.enums import SuffixType
from checkmate.url.domain.public_suffix import PublicSuffix


class TestPublicSuffix:
    def test_suffix_types(self, suffix):
        assert PublicSuffix.suffix_type(suffix.raw) == suffix.type

    @pytest.mark.parametrize("icann_only", (True, False))
    def test_is_suffix(self, suffix, icann_only):
        is_suffix = suffix.type == SuffixType.ICANN if icann_only else bool(suffix.type)

        assert PublicSuffix.is_suffix(suffix.raw, icann_only) == is_suffix

    @pytest.mark.parametrize("icann_only", (True, False))
    @pytest.mark.parametrize("prefix", ("www.", ""))
    def test_has_suffix(self, prefix, suffix, icann_only):
        domain = DomainCore(f"{prefix}{suffix.raw}")

        # Anything that has an icann suffix at all has a suffix. There's no
        # point in distinguishing between ICANN and private
        assert PublicSuffix.has_suffix(DomainCore(domain)) == bool(suffix.suffix)

    @pytest.mark.parametrize("icann_only", (True, False))
    @pytest.mark.parametrize("prefix", ("www.", ""))
    def test_get_suffix(self, prefix, suffix, icann_only):
        domain = DomainCore(f"{prefix}{suffix.raw}")

        expected_suffix = suffix.icann_suffix if icann_only else suffix.suffix

        assert PublicSuffix.get_suffix(domain, icann_only) == expected_suffix

    def test_rule_parsing(self):
        lines = """
        // ===BEGIN ICANN DOMAINS===
        com
        co.uk
        // ===END ICANN DOMAINS===
        // ===BEGIN PRIVATE DOMAINS===
        example.com
        *.example.net
        
        !exception.example.net
        // ===END PRIVATE DOMAINS===
        """
        lines = [line.strip() for line in lines.split("\n")]

        rules, longest_rule = PublicSuffix.parse_rules(lines)

        assert longest_rule == 3
        assert rules == {
            "com": PublicSuffix.Rule(2, False, SuffixType.ICANN),
            "co.uk": PublicSuffix.Rule(3, False, SuffixType.ICANN),
            "example.com": PublicSuffix.Rule(6, False, SuffixType.PRIVATE),
            "*.example.net": PublicSuffix.Rule(7, False, SuffixType.PRIVATE),
            "exception.example.net": PublicSuffix.Rule(9, True, SuffixType.PRIVATE),
        }

    # This is kind of a gross setup, but these are values picked form the list
    # which power basically all of these tests, and cover the cases in the
    # set of rules provided to us

    Suffix = namedtuple(
        "Suffix",
        [
            "raw",  # The value to use
            "type",  # The suffix type (or none)
            "suffix",  # The suffix if you accept any suffix
            "icann_suffix",  # The suffix if you only accept ICANN suffixes
        ],
    )

    @pytest.fixture(
        params=(
            param(
                Suffix(raw="", type=None, suffix=None, icann_suffix=None),
                id="empty",
            ),
            param(
                Suffix(raw="not_a_thing", type=None, suffix=None, icann_suffix=None),
                id="not a suffix",
            ),
            param(
                Suffix(
                    raw="aero",
                    type=SuffixType.ICANN,
                    suffix="aero",
                    icann_suffix="aero",
                ),
                id="icann",
            ),
            param(
                Suffix(
                    raw="airport.aero",
                    type=SuffixType.ICANN,
                    suffix="airport.aero",
                    icann_suffix="airport.aero",
                ),
                id="icann nested",
            ),
            param(
                Suffix(
                    raw="github.io",
                    type=SuffixType.PRIVATE,
                    suffix="github.io",
                    icann_suffix="io",
                ),
                id="private",
            ),
            param(
                Suffix(
                    raw="WILD.kawasaki.jp",
                    type=SuffixType.ICANN,
                    suffix="WILD.kawasaki.jp",
                    icann_suffix="WILD.kawasaki.jp",
                ),
                id="icann wild",
            ),
            param(
                Suffix(
                    raw="WILD.compute.amazonaws.com",
                    type=SuffixType.PRIVATE,
                    suffix="WILD.compute.amazonaws.com",
                    icann_suffix="com",
                ),
                id="private wild",
            ),
            param(
                Suffix(
                    raw="city.kawasaki.jp", type=None, suffix="jp", icann_suffix="jp"
                ),
                id="icann wild exception",
            ),
        )
    )
    def suffix(self, request):
        return request.param
