"""Model for our own blocking rules."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, insert
from zope.sqlalchemy import mark_changed

from checkmate.checker.url.reason import Reason
from checkmate.db import BASE


class CustomRule(BASE):
    """Rule about blocking a particular resource."""

    __tablename__ = "custom_rule"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    # While our hashes should be unique, we might change our mind about how
    # we hash. The rule itself should stay the same
    rule = sa.Column(sa.String, nullable=False, unique=True)
    """The text of the rule"""

    # We'd like to know if we have a hash collision
    # The C collation here allows the B-Tree default indexing type to be used
    # for prefix matching. This makes searching for 'ab2d23d45a%' very quick
    # https://www.postgresql.org/docs/11/indexes-types.html
    hash = sa.Column(sa.String(collation="C"), nullable=False, unique=True, index=True)
    """A hash for quick comparison"""

    tags = sa.Column(ARRAY(sa.String, dimensions=1))
    """The list of reasons why we are blocking this"""

    @staticmethod
    def bulk_update(session, values):  # pragma: no cover
        """Create or update a number of rows at once.

        This will match on the "rule" portion and must include "hash" and
        "tags". This will not delete any rows.

        :param session: DB session to execute within
        :param values: A list of dicts of columns to update
        """
        stmt = insert(CustomRule).values(values)
        stmt = stmt.on_conflict_do_update(
            # Match when the rules are the same
            index_elements=["rule"],
            # Then set these elements
            set_={"hash": stmt.excluded.hash, "tags": stmt.excluded.tags},
        )

        session.execute(stmt)

        # Let SQLAlchemy know that something has changed, otherwise it will
        # never commit the transaction we are working on and it will get rolled
        # back
        mark_changed(session)

    @property
    def reasons(self):
        """Get a list of reason object for this rule."""

        return [Reason.parse(tag) for tag in self.tags]

    @staticmethod
    def find_matches(session, hex_hashes):
        """Find matching rules for the specified hashes.

        :param session: DB session to execute within
        :param hex_hashes: List of URL hashes to find
        :return: Iterable of matching CustomRule objects
        """
        return session.query(CustomRule).filter(CustomRule.hash.in_(hex_hashes))
