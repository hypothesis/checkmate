"""Model for our own blocking rules."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from checkmate.checker.url.reason import Reason
from checkmate.db import BASE


class CustomRule(BASE):
    """Rule about blocking a particular resource."""

    __tablename__ = "custom_rule"
    __table_args__ = (sa.Index("ix__hash", "hash"),)

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    # While our hashes should be unique, we might change our mind about how
    # we hash. The rule itself should stay the same
    rule = sa.Column(sa.String, nullable=False, unique=True)
    """The text of the rule"""

    # We'd like to know if we have a hash collision
    # The C collation here allows the B-Tree default indexing type to be used
    # for prefix matching. This makes searching for 'ab2d23d45a%' very quick
    hash = sa.Column(sa.String(collation="C"), nullable=False, unique=True)
    """A hash for quick comparison"""

    tags = sa.Column(ARRAY(sa.String, dimensions=1))
    """The list of reasons why we are blocking this"""

    @property
    def reasons(self):  # pragma: no cover
        """Get a list of reason object for this rule."""

        return [Reason.parse(tag) for tag in self.tags]
