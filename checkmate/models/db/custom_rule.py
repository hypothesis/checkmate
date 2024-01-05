"""Model for our own blocking rules."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from checkmate.db import Base
from checkmate.models.db.mixins import BulkUpsertMixin, HashMatchMixin
from checkmate.models.reason import Reason


class CustomRule(Base, HashMatchMixin, BulkUpsertMixin):
    """Rule about blocking a particular resource."""

    BULK_UPSERT_INDEX_ELEMENTS = ["rule"]
    BULK_UPSERT_UPDATE_ELEMENTS = ["hash", "tags"]

    __tablename__ = "custom_rule"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    hash = HashMatchMixin.hash_column(unique=True)
    """A hash for quick comparison."""

    # While our hashes should be unique, we might change our mind about how
    # we hash. The rule itself should stay the same
    rule = sa.Column(sa.String, nullable=False, unique=True)
    """The text of the rule"""

    tags = sa.Column(ARRAY(sa.String, dimensions=1))
    """The list of reasons why we are blocking this"""

    @property
    def reasons(self):
        """Get a list of reason objects for this rule."""

        return [Reason.parse(tag) for tag in self.tags]
