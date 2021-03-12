import pytest

from checkmate.exceptions import MalformedURL
from checkmate.url.canonicalize import CanonicalURL


class TestCanonicalURL:
    # Taken from: https://cloud.google.com/web-risk/docs/urls-hashing#to_canonicalize_the_path
    # With some extras of our own
    @pytest.mark.parametrize(
        "url,canonical_url",
        (
            ("http://host/%25%32%35", "http://host/%25"),
            ("http://host/%25%32%35%25%32%35", "http://host/%25%25"),
            ("http://host/%2525252525252525", "http://host/%25"),
            ("http://host/asdf%25%32%35asd", "http://host/asdf%25asd"),
            ("http://host/%%%25%32%35asd%%", "http://host/%25%25%25asd%25%25"),
            ("http://www.google.com/", "http://www.google.com/"),
            (
                "http://%31%36%38%2e%31%38%38%2e%39%39%2e%32%36/%2E%73%65%63%75%72%65/%77%77%77%2E%65%62%61%79%2E%63%6F%6D/",
                "http://168.188.99.26/.secure/www.ebay.com/",
            ),
            (
                "http://195.127.0.11/uploads/%20%20%20%20/.verify/.eBaysecure=updateuserdataxplimnbqmn-xplmvalidateinfoswqpcmlx=hgplmcx/",
                "http://195.127.0.11/uploads/%20%20%20%20/.verify/.eBaysecure=updateuserdataxplimnbqmn-xplmvalidateinfoswqpcmlx=hgplmcx/",
            ),
            (
                "http://host%23.com/%257Ea%2521b%2540c%2523d%2524e%25f%255E00%252611%252A22%252833%252944_55%252B",
                "http://host%23.com/~a!b@c%23d$e%25f^00&11*22(33)44_55+",
            ),
            ("http://www.google.com/blah/..", "http://www.google.com/"),
            ("www.google.com/", "http://www.google.com/"),
            ("www.google.com", "http://www.google.com/"),
            ("http://www.evil.com/blah#frag", "http://www.evil.com/blah"),
            ("http://www.GOOgle.com/", "http://www.google.com/"),
            ("http://www.google.com.../", "http://www.google.com/"),
            (
                "http://www.google.com/foo\tbar\rbaz\n2",
                "http://www.google.com/foobarbaz2",
            ),
            ("http://www.google.com/q?", "http://www.google.com/q?"),
            ("http://www.google.com/q?r?", "http://www.google.com/q?r?"),
            ("http://www.google.com/q?r?s", "http://www.google.com/q?r?s"),
            ("http://evil.com/foo#bar#baz", "http://evil.com/foo"),
            ("http://evil.com/foo),", "http://evil.com/foo),"),
            ("http://evil.com/foo?bar),", "http://evil.com/foo?bar),"),
            ("http://\x01\x80.com/", "http://%01%80.com/"),
            ("http://notrailingslash.com", "http://notrailingslash.com/"),
            ("http://www.gotaport.com:1234/", "http://www.gotaport.com/"),
            ("  http://www.google.com/  ", "http://www.google.com/"),
            ("http:// leadingspace.com/", "http://%20leadingspace.com/"),
            ("http://%20leadingspace.com/", "http://%20leadingspace.com/"),
            ("%20leadingspace.com/", "http://%20leadingspace.com/"),
            ("https://www.securesite.com/", "https://www.securesite.com/"),
            ("http://host.com/ab%23cd", "http://host.com/ab%23cd"),
            (
                "http://host.com//twoslashes?more//slashes",
                "http://host.com/twoslashes?more//slashes",
            ),
            # Many flavours of IP addresses (added by us mostly)
            ("http://3279880203/blah", "http://195.127.0.11/blah"),
            ("http://0303.0177.0000.0013/blah", "http://195.127.0.11/blah"),
            ("http://030337600013/blah", "http://195.127.0.11/blah"),
            ("http://0xc3.0x7f.0x00.0x0b/blah", "http://195.127.0.11/blah"),
            ("http://0xc37f000b/blah", "http://195.127.0.11/blah"),
            ("http://192.168.2.1/uploads/", "http://192.168.2.1/uploads/"),
            ("http://0x7F.0.0.1/uploads/", "http://127.0.0.1/uploads/"),
            ("http://0x7F.0.0.0x1/uploads/", "http://127.0.0.1/uploads/"),
            ("http://10.0.0.1/uploads/", "http://10.0.0.1/uploads/"),
            (
                "http://022.101.31.153/uploads/",
                "http://18.101.31.153/uploads/",
            ),  # Leading 0 as octal
            # Punycode testing (added by us)
            ("http://ümlaut.com", "http://xn--mlaut-jva.com/"),
            # Some unspecified behavior around badly formatted URLs (added by
            # us). The logic being, if Chrome will open it, we should check it
            ("/example.com", "http://example.com/"),
            ("//example.com", "http://example.com/"),
            ("///example.com", "http://example.com/"),
            ("http:/example.com", "http://example.com/"),
            ("http:///example.com", "http://example.com/"),
            ("http:/", "http:///"),
            ("http://", "http:///"),
            ("/", "http:///"),
            ("//", "http:///"),
            (
                "https://www.tumblr.com/search/‘question?’/post_page/2",
                "https://www.tumblr.com/search/%2018question?%2019/post_page/2",
            ),
            # Chrome will fail with this one, we should not raise an unexpected exception
            (
                "https%3A%2F%2Fwww.google.com",
                "http://https://www.google.com/",
            ),
        ),
    )
    def test_canonicalise(self, url, canonical_url):
        result = CanonicalURL.canonicalize(url)

        assert result == canonical_url

    def test_canonical_split(self):
        # We don't need to go nuts here, as this is well covered above

        parts = CanonicalURL.canonical_split(
            "http:/example.com/path/abc;path_param?a=b#foo"
        )
        assert parts == ("http", "example.com", "/path/abc", "path_param", "a=b", None)

    def test_canonicalise_invalid(self):
        with pytest.raises(MalformedURL):
            CanonicalURL.canonicalize("http://example.com]")
