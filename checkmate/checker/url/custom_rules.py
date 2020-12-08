"""A checker based on our own curated ruleset."""

from checkmate.models.db.custom_rule import CustomRule
from checkmate.url import hash_for_rule


class CustomRules:
    """A checker based on our own curated ruleset."""

    def __init__(self, session):
        """Create a new CustomRules object.

        :param session: A DB session to work in
        """
        self._session = session

    def check_url(self, hex_hashes):
        """Check for reasons to block a URL based on it's hashes.

        :param hex_hashes: A list of hashes for a URL
        :returns: A generator of Reason objects
        """
        hits = CustomRule.find_matches(self._session, hex_hashes)

        for hit in hits:
            yield from hit.reasons

    def update_from_blocklist_rules(self, raw_rules):  # pragma: no cover
        """Update the DB with a series of rules."""

        # Note: This currently has no way of removing things from the DB
        # Soon this won't matter as we won't be doing this any more

        CustomRule.bulk_update(
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
