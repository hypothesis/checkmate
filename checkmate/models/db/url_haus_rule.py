"""Model for blocking based on URLHaus."""

import sqlalchemy as sa

from checkmate.db import BASE
from checkmate.models.db.mixins import BulkUpsertMixin, HashMatchMixin


class URLHausRule(BASE, HashMatchMixin, BulkUpsertMixin):
    """Rule about blocking a particular resource."""

    BULK_UPSERT_INDEX_ELEMENTS = ["id"]
    BULK_UPSERT_UPDATE_ELEMENTS = ["rule", "hash"]

    __tablename__ = "urlhaus_rule"

    id = sa.Column(sa.Integer, primary_key=True)
    """The ID provided by URLHaus."""

    hash = HashMatchMixin.hash_column()
    """A hash for quick comparison."""

    rule = sa.Column(sa.String, nullable=False)
    """The text of the rule."""

    @classmethod
    def truncate(cls, session):
        session.execute("TRUNCATE urlhaus_rule")
