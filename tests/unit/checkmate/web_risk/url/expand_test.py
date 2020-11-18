import pytest

from checkmate.web_risk.url.expand import ExpandURL


class TestExpand:
    @pytest.mark.parametrize(
        "url,expansions",
        (
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
        ),
    )
    def test_it(self, url, expansions):
        results = ExpandURL.expand(url)

        assert tuple(results) == expansions
