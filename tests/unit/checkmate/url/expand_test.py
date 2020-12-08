import pytest

from checkmate.url.expand import ExpandURL

# Taken from: https://cloud.google.com/web-risk/docs/urls-hashing#suffixprefix_expressions
TEST_SET = (
    (
        "http://a.b.c/1/2.html?param=1",
        (
            "a.b.c/1/2.html?param=1",
            "a.b.c/1/2.html",
            "a.b.c/",
            "a.b.c/1/",
            "b.c/1/2.html?param=1",
            "b.c/1/2.html",
            "b.c/",
            "b.c/1/",
        ),
    ),
    (
        "http://a.b.c.d.e.f.g/1.html",
        (
            "a.b.c.d.e.f.g/1.html",
            "a.b.c.d.e.f.g/",
            "c.d.e.f.g/1.html",
            "c.d.e.f.g/",
            "d.e.f.g/1.html",
            "d.e.f.g/",
            "e.f.g/1.html",
            "e.f.g/",
            "f.g/1.html",
            "f.g/",
        ),
    ),
    (
        "http://1.2.3.4/1/",
        (
            "1.2.3.4/1/",
            "1.2.3.4/",
        ),
    ),
    ("http:///", ("/",)),
)


class TestExpand:
    @pytest.mark.parametrize("url,expansions", TEST_SET)
    def test_expand(self, url, expansions):
        results = ExpandURL.expand(url)

        assert tuple(results) == expansions

    @pytest.mark.parametrize("url,expansions", TEST_SET)
    def test_expand_single(self, url, expansions):
        result = ExpandURL.expand_single(url)

        assert result == expansions[0]
