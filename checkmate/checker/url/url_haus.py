"""URLHaus (https://urlhaus.abuse.ch/) based checker."""

from tempfile import TemporaryDirectory

from checkmatelib.url import hash_for_rule

from checkmate.checker.pipeline import Download, Pipeline, ReadCSVFile, UnzipFile
from checkmate.checker.url._hashed_url_checker import HashedURLChecker
from checkmate.models import Reason, URLHausRule


class URLHaus(HashedURLChecker):
    """A checker which works against and updates URLHaus rules."""

    # The columns provided in the CSV from URLHaus are:
    # id, dateadded, url, url_status, threat, tags, urlhaus_link, reporter
    COLUMN_ID = 0
    COLUMN_URL = 2

    INITIAL_FEED = Pipeline(
        [
            Download("https://urlhaus.abuse.ch/downloads/csv/", timeout=30),
            UnzipFile("csv.txt"),
            ReadCSVFile(),
        ]
    )

    UPDATE_FEED = Pipeline(
        [
            Download("https://urlhaus.abuse.ch/downloads/csv_recent/", timeout=30),
            ReadCSVFile(),
        ]
    )

    def check_url(self, hex_hashes):
        """Check for reasons to block a URL based on it's hashes.

        :param hex_hashes: A list of hashes for a URL
        :returns: A generator of Reason objects
        """

        # All URLHaus rules are malicious, so there's no reason to find more
        # than one
        hits = URLHausRule.find_matches(self._session, hex_hashes, limit=1)

        if hits.count():
            yield Reason.MALICIOUS

    def reinitialize_db(self):
        """Completely resynchronise the DB from scratch."""

        URLHausRule.delete_all(self._session)
        return self._update(self.INITIAL_FEED)

    def update_db(self):
        """Perform a partial update of the last 30 days of data."""

        return self._update(self.UPDATE_FEED)

    def _update(self, feed):
        with TemporaryDirectory() as working_dir:
            return URLHausRule.bulk_upsert(
                session=self._session,
                values=(self._value_from_row(row) for row in feed(working_dir)),
            )

    def _value_from_row(self, row):
        expanded_url, hex_hash = hash_for_rule(raw_url=row[self.COLUMN_URL])

        return {
            "id": row[self.COLUMN_ID],
            "rule": expanded_url,
            "hash": hex_hash,
        }
