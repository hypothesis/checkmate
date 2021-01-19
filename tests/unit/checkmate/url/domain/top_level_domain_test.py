import pytest

from checkmate.url.domain._domain_core import DomainCore
from checkmate.url.domain.top_level_domain import TopLevelDomain


class TestTopLevelDomain:
    @pytest.mark.parametrize(
        "suffix,is_tld",
        (
            ("com", True),
            ("org", True),
            ("co.uk", False),
            ("example.com", False),
            (None, False),
            ("", False),
            ("iljwnerljkengr", False),
        ),
    )
    def test_is_tld(self, suffix, is_tld):
        assert TopLevelDomain.is_tld(suffix) == is_tld

    @pytest.mark.parametrize(
        "suffix,has_tld",
        (
            ("org", False),  # This is a TLD, it doesn't have one
            ("example.org", True),
            ("www.example.org", True),
            ("www.example", False),
            ("www.example.local", False),
            (None, False),
            ("", False),
            ("iljwnerljkengr", False),
        ),
    )
    def test_has_tld(self, suffix, has_tld):
        assert TopLevelDomain.has_tld(suffix) == has_tld

    @pytest.mark.parametrize(
        "suffix,tld",
        (
            ("org", None),  # This is a TLD, it doesn't have one
            ("example.org", "org"),
            # If we're given a domain core it will save a tiny amount of time
            # recreating one
            (DomainCore("example.org"), "org"),
            ("www.example.org", "org"),
            ("www.example", None),
            ("www.example.local", None),
            (None, None),
            ("", None),
            ("iljwnerljkengr", None),
        ),
    )
    def test_get_tld(self, suffix, tld):
        assert TopLevelDomain.get_tld(suffix) == tld
