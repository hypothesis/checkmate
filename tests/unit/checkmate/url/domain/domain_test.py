import pytest
from h_matchers import Any

from checkmate.url import Domain
from checkmate.url.domain.enums import SuffixType


class TestDomain:
    # These methods are quite often really just combinations of other things
    # so we'll be giving some a quite light touch

    @pytest.mark.parametrize(
        "domain,is_public",
        (
            ("www.example.com", True),
            ("  www.whitespace.com", True),
            ("216.58.212.206", True),
            ("192.168.34.11", False),
            ("bad.-hyphen.com", False),
            ("plausable.but-wrong.dato", False),
            ("random_hostname", False),
            ("<html>", False),
        ),
    )
    def test_is_public(self, domain, is_public):
        assert Domain(domain).is_public == is_public

    @pytest.mark.parametrize(
        "domain,is_fqdn",
        (
            ("com", False),
            ("co.uk", False),
            ("more.com", True),
            ("www.example.com", True),
            ("  www.whitespace.com", True),
            ("216.58.212.206", False),  # IPs are not fully qualified
            ("bad.-hyphen.com", False),
            ("plausable.but-wrong.dato", False),
            ("random_hostname", False),
            ("<html>", False),
        ),
    )
    def test_is_fully_qualified(self, domain, is_fqdn):
        assert Domain(domain).is_fully_qualified == is_fqdn

    @pytest.mark.parametrize(
        "domain,tld",
        (
            ("www.example.com", "com"),
            ("com", "com"),
            ("www.example.not_a_tld", None),
            ("10.0.0.1", None),
        ),
    )
    def test_tld(self, domain, tld):
        assert Domain(domain).tld == tld

    @pytest.mark.parametrize(
        "domain,public_suffix",
        (
            ("com", "com"),
            ("co.uk", "co.uk"),
            ("www.example.com", "com"),
            ("www.example.co.uk", "co.uk"),
            ("page.github.io", "github.io"),
            ("nonsense", None),
            ("10.0.0.1", None),
        ),
    )
    def test_public_suffix(self, domain, public_suffix):
        assert Domain(domain).public_suffix == public_suffix

    @pytest.mark.parametrize(
        "domain,icann_suffix",
        (
            ("com", "com"),
            ("co.uk", "co.uk"),
            ("www.example.com", "com"),
            ("www.example.co.uk", "co.uk"),
            ("page.github.io", "io"),
            ("nonsense", None),
            ("10.0.0.1", None),
        ),
    )
    def test_icann_suffix(self, domain, icann_suffix):
        assert Domain(domain).icann_suffix == icann_suffix

    @pytest.mark.parametrize(
        "domain,suffix_type",
        (
            ("com", SuffixType.ICANN),
            ("www.example.com", SuffixType.ICANN),
            ("www.example.co.uk", SuffixType.ICANN),
            ("page.github.io", SuffixType.PRIVATE),
            ("github.io", SuffixType.PRIVATE),
            ("nonsense", None),
            ("10.0.0.1", None),
        ),
    )
    def test_suffix_type(self, domain, suffix_type):
        assert Domain(domain).suffix_type == suffix_type

    @pytest.mark.parametrize(
        "domain,icann_only,sub_domains,root_domain",
        (
            ("www.example.com", False, ["www"], "example.com"),
            ("a.page.github.io", False, ["a"], "page.github.io"),
            ("github.io", False, [], "github.io"),
            ("a.page.github.io", True, ["a", "page"], "github.io"),
            # Lets say IPs are their own root domain
            ("10.0.0.1", False, [], "10.0.0.1"),
            # Is there any sensible way to deal with things without public
            # suffixes? We don't know where to start or stop here
            ("my_home_pc", False, [], "my_home_pc"),
            ("a.b.c.d.e.my_home_pc.local", False, [], "a.b.c.d.e.my_home_pc.local"),
        ),
    )
    def test_split_domain(self, domain, icann_only, sub_domains, root_domain):
        values = Domain(domain).split_domain(icann_only)

        assert values == (sub_domains, root_domain)

    @pytest.mark.parametrize(
        "domain,root_domain",
        (
            ("www.example.com", "example.com"),
            ("www2.example.com", "example.com"),
            ("a.b.example.com", "example.com"),
            ("a.b.c.page.github.io", "page.github.io"),
            # Lets say IPs are their own root domain
            ("10.0.0.1", "10.0.0.1"),
            # Is there any sensible way to deal with things without public
            # suffixes? We don't know where to start or stop here
            ("my_home_pc", "my_home_pc"),
            ("a.b.c.d.e.my_home_pc.local", "a.b.c.d.e.my_home_pc.local"),
        ),
    )
    def test_root_domain(self, domain, root_domain):
        assert Domain(domain).root_domain == root_domain

    def test_as_dict(self):
        # Not really going to go to town on this just yet, the exact contents
        # aren't used by anyone. It's just a good way to dump them right now.
        assert Domain("www.example.com").as_dict() == Any.dict()
