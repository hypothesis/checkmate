"""Model for blocking based on URLHaus."""

import sqlalchemy as sa

from checkmate.db import Base
from checkmate.models.db.mixins import BulkUpsertMixin, HashMatchMixin


class URLHausRule(Base, HashMatchMixin, BulkUpsertMixin):
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
    def delete_all(cls, session):
        """Remove all rows from this table."""

        # Don't use truncate as this will cause the transaction to lock
        # reads while we are filling the DB back up. See:
        # https://www.postgresql.org/docs/11/explicit-locking.html
        # Or for a slightly friendlier summary:
        # https://www.citusdata.com/blog/2018/02/15/when-postgresql-blocks/

        session.query(cls).delete()
