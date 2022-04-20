"""A checker based on our own curated ruleset."""
import re
from logging import getLogger

import requests
from checkmatelib.url import hash_for_rule

from checkmate.checker.url._hashed_url_checker import HashedURLChecker
from checkmate.models import CustomRule, Reason


class CustomRules(HashedURLChecker):
    """A checker based on our own curated ruleset."""

    def check_url(self, hex_hashes):
        """Check for reasons to block a URL based on it's hashes.

        :param hex_hashes: A list of hashes for a URL
        :returns: A generator of Reason objects
        """
        hits = CustomRule.find_matches(self._session, hex_hashes)

        for hit in hits:
            yield from hit.reasons

    def load_simple_rule_url(self, source_url):  # pragma: no cover
        """Update the DB with the content hosted at a specified URL."""
        raw_rules = BlocklistParser.parse_url(source_url)

        if not raw_rules:
            return None

        self.load_simple_rules(raw_rules)

        return raw_rules

    def load_simple_rules(self, raw_rules):  # pragma: no cover
        """Update the DB with a series of rules."""

        # Note: This currently has no way of removing things from the DB
        # Soon this won't matter as we won't be doing this any more

        CustomRule.bulk_upsert(
            self._session,
            values=[
                self._value_from_domain(domain, reason)
                for domain, reason in raw_rules.items()
            ],
        )

    @staticmethod
    def _value_from_domain(domain, reason):  # pragma: no cover
        if "*" in domain:
            # It's a wild card!
            domain = domain.lstrip("*")
            if "*" in domain:
                raise ValueError("Cannot convert non prefix wildcard")

        # Using a raw domain as a URL is close enough, as it's subject
        # to normalisation anyway
        expanded_url, hex_hash = hash_for_rule(raw_url=domain)

        return {
            "rule": expanded_url,
            "hash": hex_hash,
            "tags": [reason.value],
        }


# This is going to be removed very soon, so lets not test it


class BlocklistParser:  # pragma: no cover
    """A blocklist which URLs can be checked against.

    For details of how to change the blocklist see:
      * https://stackoverflow.com/c/hypothesis/questions/102/250

    And is downloaded locally, via supervisor using `bin/fetch-blocklist`
    """

    LOG = getLogger(__name__)
    LINE_PATTERN = re.compile(r"^(\S+)\s+(\S+)(?:\s*#.*)?$")

    @classmethod
    def parse_url(cls, source_url):
        """Parse the contents of a text file hosted at the specified URL."""

        if not source_url:
            cls.LOG.info("Not updating blocklist as the URL is blank")
            return None

        with requests.get(source_url, stream=True, timeout=5) as response:
            response.raise_for_status()

            lines = (line.decode("utf-8") for line in response.iter_lines())

            return dict(cls.parse_lines(lines))

    @classmethod
    def parse_lines(cls, lines):
        """Parse raw lines."""

        for line in lines:
            line = line.strip()

            if not line or line.startswith("#"):
                # Empty or comment line.
                continue

            match = cls.LINE_PATTERN.match(line)
            if match:
                raw_rule, reason = match.group(1), match.group(2)
            else:
                cls.LOG.warning("Cannot parse blocklist file line: '%s'")
                continue

            yield raw_rule, Reason.parse(reason)
