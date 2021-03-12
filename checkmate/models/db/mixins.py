"""Mixins to enhance model objects."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from zope.sqlalchemy import mark_changed


class HashMatchMixin:
    """A mixin for models which want to support hash based URL comparisons.

    Your subclass must have a column like this:
        hash = HashMatchMixin.hash_column()
    """

    @staticmethod
    def hash_column(unique=False):
        """Return a column suitable for hashing which you must call "hash"."""

        # The C collation here allows the B-Tree default indexing type to be
        # used for prefix matching. This makes searching for 'ab2d23d45a%'
        # very quick: https://www.postgresql.org/docs/11/indexes-types.html
        return sa.Column(
            sa.String(collation="C"), nullable=False, index=True, unique=unique
        )

    @classmethod
    def find_matches(cls, session, hex_hashes, limit=None):
        """Find matching rules for the specified hashes.

        :param session: DB session to execute within
        :param hex_hashes: List of URL hashes to find
        :param limit: Limit the number of returned values
        :return: Iterable of matching CustomRule objects
        """

        query = session.query(cls).filter(cls.hash.in_(hex_hashes))

        if limit:
            query = query.limit(limit)

        return query


class BulkUpsertMixin:
    """A mixin for models that want to support bulk upserting."""

    BULK_UPSERT_INDEX_ELEMENTS = None
    """Elements to detect collisions on."""

    BULK_UPSERT_UPDATE_ELEMENTS = None
    """Elements to set in the event of a collision."""

    BLOCK_SIZE = 1000
    """Numer of elements to attempt to update in one go."""

    @classmethod
    def bulk_upsert(cls, session, values):
        """Create or update a number of rows at once.

        This will match on the "rule" portion and must include "hash" and
        "tags". This will not delete any rows.

        :param session: DB session to execute within
        :param values: A list of dicts of columns to update
        :raise NotImplementedError: If you have not provided the expected class
            values
        """

        if not cls.BULK_UPSERT_INDEX_ELEMENTS or not cls.BULK_UPSERT_UPDATE_ELEMENTS:
            raise NotImplementedError(
                "You must provide the correct elements for this mixin to work"
            )

        total_items = 0
        for block in cls._chunk(values):
            total_items += len(block)

            cls._bulk_upsert(
                session,
                block,
                index_elements=cls.BULK_UPSERT_INDEX_ELEMENTS,
                update_elements=cls.BULK_UPSERT_UPDATE_ELEMENTS,
            )

        return total_items

    @classmethod
    def _chunk(cls, values):
        block = []

        for value in values:
            block.append(value)

            if len(block) >= cls.BLOCK_SIZE:
                yield block
                block = []

        if block:
            yield block

    @classmethod
    def _bulk_upsert(cls, session, values, index_elements, update_elements):
        stmt = insert(cls).values(values)

        stmt = stmt.on_conflict_do_update(
            # Match when the rules are the same
            index_elements=index_elements,
            # Then set these elements
            set_={
                element: getattr(stmt.excluded, element) for element in update_elements
            },
        )

        session.execute(stmt)

        # Let SQLAlchemy know that something has changed, otherwise it will
        # never commit the transaction we are working on and it will get rolled
        # back
        mark_changed(session)


class JSONAPIMixin:
    """A mixin for models to add JSON:API related functions."""

    def to_json_api(self):
        """Create a JSON:API resource dict for this object."""

        if not self.id:
            raise ValueError(
                "An ID is mandatory to serialise an object in JSON:API. Have you flushed the DB?"
            )

        return {
            "type": self.__class__.__name__,
            "id": self.id,
            "attributes": {
                key: getattr(self, key)
                for key in self.__table__.columns.keys()
                if key != "id"
            },
        }
