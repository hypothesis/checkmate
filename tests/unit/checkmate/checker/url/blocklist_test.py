import os

import pytest
from h_matchers import Any

from checkmate.checker.url.blocklist import Blocklist
from checkmate.checker.url.reason import Reason
from checkmate.exceptions import MalformedURL


class TestBlocklist:
    def test_it_can_start_without_a_file(self):
        blocklist = Blocklist("missing.txt")

        assert blocklist.domains == {}

    def test_it_reloads_when_the_file_changes(self, blocklist_file):
        blocklist = Blocklist(blocklist_file)
        assert blocklist.domains  # Check we've loaded something
        blocklist.clear()
        blocklist_file.touch()  # Reset the access times

        list(blocklist.check_url("foo"))

        # The original set has not been reloaded
        # assert blocklist.domains

    def test_it_does_not_reload_if_the_file_is_the_same(self, blocklist_file):
        blocklist = Blocklist(blocklist_file)
        assert blocklist.domains  # Check we've loaded something
        blocklist.clear()

        list(blocklist.check_url("foo"))

        # The original set has not been reloaded
        assert blocklist.domains == {}

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
            ("example.com other", Reason.OTHER),
            ("example.com right-format-wrong-value", Reason.OTHER),
            # Comment
            ("# any old comment", None),
            # Unparsable
            ("example.com", None),
            ("example.com too many parts", None),
            # Allowed for viahtml
            ("example.com  media-video", None),
        ),
    )
    def test_file_loading(self, tmp_path, line, reason):
        filename = tmp_path / "blocklist.txt"
        filename.write_text(line)

        blocklist = Blocklist(filename)

        assert blocklist.domains == ({"example.com": reason} if reason else {})

    @pytest.mark.parametrize(
        "line,reason",
        (
            ("*.example.com publisher-blocked", Reason.PUBLISHER_BLOCKED),
            ("*.example.com rubbish", Reason.OTHER),
            ("*.example.com", None),
        ),
    )
    def test_file_loading_wildcards(self, tmp_path, line, reason):
        filename = tmp_path / "blocklist.txt"
        filename.write_text(line)

        blocklist = Blocklist(filename)

        if not reason:
            assert blocklist.patterns == {}
        else:
            assert len(blocklist.patterns) == 1
            ((domain, found_reason),) = blocklist.patterns.items()
            assert found_reason == reason
            # This regex happens to be what `fnmatch.translate` spits out
            assert domain.pattern == r"(?s:.*\.example\.com)\Z"

    @pytest.mark.parametrize(
        "url,reasons",
        (
            ("https://www.example.com", [Reason.MALICIOUS]),
            ("http://www.example.com", [Reason.MALICIOUS]),
            ("//www.example.com", [Reason.MALICIOUS]),
            ("www.example.com", [Reason.MALICIOUS]),
            ("http://www.example.com/path", [Reason.MALICIOUS]),
            ("http://www.example.com/path?a=b", [Reason.MALICIOUS]),
            # Sub-domains don't count
            ("http://example.com", []),
            ("http://example.org", []),
            # Wildcard matching
            ("anything.example.net", [Reason.OTHER]),
            ("anything.nested.example.net", [Reason.OTHER]),
            ("thisisfineexample.net", []),
        ),
    )
    def test_url_matching(self, url, reasons):
        blocklist = Blocklist("missing.txt")
        blocklist.add_domain("www.example.com", Reason.MALICIOUS)
        blocklist.add_domain("*.example.net", Reason.OTHER)

        assert blocklist.check_url(url) == Any.generator.containing(reasons).only()

    @pytest.mark.parametrize("url", ("http://", "http:///", "http:///foo", "/"))
    def test_it_raises_MalformedURL_for_bad_urls(self, url):
        blocklist = Blocklist("missing.txt")

        with pytest.raises(MalformedURL):
            tuple(blocklist.check_url(url))

    @pytest.fixture
    def blocklist_file(self, tmp_path):
        blocklist_file = tmp_path / "blocklist.txt"
        blocklist_file.write_text("example.com other")

        # Make the file very old
        os.utime(blocklist_file, (0, 0))

        return blocklist_file
