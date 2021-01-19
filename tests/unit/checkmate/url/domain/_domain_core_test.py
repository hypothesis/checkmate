import pytest

from checkmate.url.domain._domain_core import DomainCore


class TestDomainCore:
    @pytest.mark.parametrize(
        "raw_domain,domain",
        (
            ("domain_name", "domain_name"),
            ("domain_name:1234", "domain_name"),
        ),
    )
    def test_it_strips_ports(self, raw_domain, domain):
        assert DomainCore(raw_domain) == domain

    @pytest.mark.parametrize(
        "domain,is_valid",
        (
            # Normal parts
            ("www.example.com", True),
            ("www.example", True),
            ("www", True),
            ("www.", False),
            ("10.0.0.1", True),
            ("10.0.0.1.0.01", True),  # Not an IP, but totally valid
            # Bad chars (just a few)
            ("under_score", False),
            ("star*", False),
            ("bang!", False),
            ("a space", False),
            ("<html>", False),
            # Too long
            ("y" * 63, True),
            ("n" * 64, False),
            ("y." * 126 + "y", True),  # Max length is 253 ASCII characters
            ("n." * 126 + "nn", False),
        ),
    )
    def test_is_valid(self, domain, is_valid):
        assert DomainCore(domain).is_valid == is_valid

    @pytest.mark.parametrize(
        "middle,is_valid",
        (
            ("-prefixdash", False),
            ("infix-dash", True),
            ("postfixdash-", False),
        ),
    )
    @pytest.mark.parametrize("prefix", ("www.", ""))
    @pytest.mark.parametrize("suffix", (".com", ""))
    def test_is_valid_with_dashes(self, prefix, middle, suffix, is_valid):
        domain = f"{prefix}{middle}{suffix}"

        assert DomainCore(domain).is_valid == is_valid

    @pytest.mark.parametrize(
        "domain,is_ipv4",
        (
            ("0.0.0.0", True),
            ("255.255.255.255", True),
            # Values too high
            ("256.256.256.256", False),
            # Wrong length
            ("1.2.3.4.5", False),
            ("1.2.3", False),
            # We assume we have been normalised, so none of this should count
            ("0x1.0x2.0x3.0x4", False),
            ("0104FEA6", False),
            # Nope
            ("words", False),
            ("10..10.10", False),
        ),
    )
    def test_is_ip_v4(self, domain, is_ipv4):
        assert DomainCore(domain).is_ip_v4 == is_ipv4

    @pytest.mark.parametrize(
        "domain,is_private_ipv4",
        (
            ("0.0.0.0", True),  # Kind of not really an IP but for our purposes yes
            # 127 range
            ("126.255.255.255", False),
            ("127.0.0.0", True),
            ("127.255.255.255", True),
            ("128.0.0.0", False),
            # 10 range
            ("9.255.255.255", False),
            ("10.0.0.0", True),
            ("10.255.255.255", True),
            ("11.0.0.0", False),
            # 172 range
            ("172.15.255.255", False),
            ("172.16.0.0", True),
            ("172.31.255.255", True),
            ("172.32.0.0", False),
            # 192 range
            ("192.167.255.255", False),
            ("192.168.0.0", True),
            ("192.168.255.255", True),
            ("192.169.0.0", False),
            # Nope
            ("words", False),
        ),
    )
    def test_is_private_ip_v4(self, domain, is_private_ipv4):
        assert DomainCore(domain).is_private_ip_v4 == is_private_ipv4

    def test_labels(self):
        assert DomainCore("a.b.c").labels == ["a", "b", "c"]

    @pytest.mark.parametrize(
        "domain,depth,suffix",
        (
            ("192.168.0.1", 2, None),
            ("a.b.c", -2, ""),
            ("a.b.c", -1, ""),
            ("a.b.c", 0, ""),
            ("a.b.c", 1, "c"),
            ("a.b.c", 2, "b.c"),
            ("a.b.c", 3, "a.b.c"),
            ("a.b.c", 4, "a.b.c"),
        ),
    )
    def test_suffix(self, domain, depth, suffix):
        assert DomainCore(domain).suffix(depth) == suffix

    @pytest.mark.parametrize(
        "domain,arg,value,suffixes",
        (
            ("a.b.c", None, None, ["c", "b.c", "a.b.c"]),
            ("10.0.0.1", None, None, []),  # IPs don't have suffixes
            ("a.b.c", "include_domain", True, ["c", "b.c", "a.b.c"]),
            ("a.b.c", "include_domain", False, ["c", "b.c"]),
            ("a.b.c", "min_depth", -1, ["c", "b.c", "a.b.c"]),
            ("a.b.c", "min_depth", 0, ["c", "b.c", "a.b.c"]),
            ("a.b.c", "min_depth", 1, ["c", "b.c", "a.b.c"]),
            ("a.b.c", "min_depth", 2, ["b.c", "a.b.c"]),
            ("a.b.c", "min_depth", 3, ["a.b.c"]),
            ("a.b.c", "min_depth", 4, []),
            ("a.b.c", "max_depth", -1, []),
            ("a.b.c", "max_depth", 0, []),
            ("a.b.c", "max_depth", 1, ["c"]),
            (
                "a.b.c",
                "max_depth",
                2,
                [
                    "c",
                    "b.c",
                ],
            ),
            ("a.b.c", "max_depth", 3, ["c", "b.c", "a.b.c"]),
            ("a.b.c", "max_depth", 4, ["c", "b.c", "a.b.c"]),
        ),
    )
    def test_suffixes(self, domain, arg, value, suffixes):
        kwargs = {arg: value} if arg else {}

        assert list(DomainCore(domain).suffixes(**kwargs)) == suffixes

    def test_repr(self):
        domain = DomainCore("example.com")

        assert DomainCore.__name__ in repr(domain)
        assert "example.com" in repr(domain)
