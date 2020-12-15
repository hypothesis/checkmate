from unittest.mock import sentinel

import pytest
from h_matchers import Any
from httpretty import httprettified, httpretty
from pkg_resources import resource_string

from checkmate.checker.url import URLHaus
from checkmate.checker.url.reason import Reason


class TestURLHaus:
    def test_check_url_with_hits(self, URLHausRule):
        URLHausRule.find_matches.return_value.count.return_value = 2

        response = URLHaus(sentinel.db_session).check_url(["hex_hash"])

        assert response == Any.generator.containing([Reason.MALICIOUS]).only()
        # The above will exhaust the generator and allow us to make assertions
        # about the call
        URLHausRule.find_matches.assert_called_once_with(
            sentinel.db_session, ["hex_hash"], limit=1
        )

    def test_check_url_with_no_hits(self, URLHausRule):
        URLHausRule.find_matches.return_value.count.return_value = 0

        response = URLHaus(sentinel.db_session).check_url(["hex_hash"])

        assert response == Any.generator.containing([]).only()

    @httprettified
    def test_reinitialize_db(self, URLHausRule):
        httpretty.register_uri(
            httpretty.GET,
            "https://urlhaus.abuse.ch/downloads/csv/",
            body=self.read_fixture("csv.txt.zip"),
        )

        response = URLHaus(sentinel.db_session).reinitialize_db()

        URLHausRule.truncate.assert_called_once_with(sentinel.db_session)
        self.assert_expected_sync(response, URLHausRule)

    def test_partial_update(self, URLHausRule):
        httpretty.register_uri(
            httpretty.GET,
            "https://urlhaus.abuse.ch/downloads/csv_recent/",
            body=self.read_fixture("csv.txt"),
        )

        response = URLHaus(sentinel.db_session).update_db()

        URLHausRule.truncate.assert_not_called()
        self.assert_expected_sync(response, URLHausRule)

    def assert_expected_sync(self, response, URLHausRule):
        URLHausRule.bulk_upsert.assert_called_once_with(
            session=sentinel.db_session, values=Any.generator()
        )
        assert response == URLHausRule.bulk_upsert.return_value
        assert URLHausRule.updated_values == [
            {
                "hash": "7d93a7a785da3bb7fc67b08cda3368745eb7cf6155e4d8b26415680e69a3f5c6",
                "id": "904859",
                "rule": "180.112.189.18/bin.sh",
            },
            {
                "hash": "f1991c232fda31acdfb50bf118458ddfd31140649218f4774f9c98e50317a59c",
                "id": "904858",
                "rule": "117.194.161.173/bin.sh",
            },
        ]

    def read_fixture(self, name):
        return resource_string(__name__, f"fixture/{name}")

    @pytest.fixture(autouse=True)
    def URLHausRule(self, patch):
        URLHausRule = patch("checkmate.checker.url.url_haus.URLHausRule")

        # Ensure we exhaust the generator we are given like URLHausRule would
        # and grab the result

        def exhaust(session, values):
            URLHausRule.updated_values = list(values)
            return URLHausRule.bulk_upsert.return_value

        URLHausRule.bulk_upsert.side_effect = exhaust

        return URLHausRule
