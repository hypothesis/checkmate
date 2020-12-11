from unittest.mock import sentinel

import pytest
import sqlalchemy as sa
from h_matchers import Any

from checkmate.db import BASE
from checkmate.models.db.mixins import BulkUpsertMixin, HashMatchMixin


class TestHashMatchMixin:
    class TableWithHash(BASE, HashMatchMixin):
        __tablename__ = "test_table_with_hash"

        id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
        hash = HashMatchMixin.hash_column()

    def test_it_retrieves_all(self, db_session):
        items = self.TableWithHash.find_matches(
            db_session, hex_hashes=["hash_1", "hash_3"]
        )
        assert [item.hash for item in items] == Any.list.containing(
            ["hash_1", "hash_3"]
        ).only()

    def test_it_with_limit(self, db_session):
        items = self.TableWithHash.find_matches(
            db_session, hex_hashes=["hash_1", "hash_3"], limit=1
        )
        assert items.count() == 1
        assert items[0].hash in ["hash_1", "hash_3"]

    @pytest.fixture(autouse=True)
    def hashes(self, db_session):
        db_session.add_all(
            [
                self.TableWithHash(hash="hash_1"),
                self.TableWithHash(hash="hash_2"),
                self.TableWithHash(hash="hash_3"),
            ]
        )


class TestBulkUpsertMixin:
    class TableWithBulkUpsert(BASE, BulkUpsertMixin):
        __tablename__ = "test_table_with_bulk_upsert"

        BULK_UPSERT_INDEX_ELEMENTS = ["id"]
        BULK_UPSERT_UPDATE_ELEMENTS = ["name"]
        BLOCK_SIZE = 2

        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)
        other = sa.Column(sa.String)

    # Vary the block size to catch an exact multiple and multiple blocks
    @pytest.mark.parametrize("block_size", [2, 3])
    def test_it_can_be_upserted(self, db_session, block_size):
        db_session.add_all(
            [
                self.TableWithBulkUpsert(id=1, name="pre_existing_1", other="pre_1"),
                self.TableWithBulkUpsert(id=2, name="pre_existing_2", other="pre_2"),
            ]
        )
        db_session.flush()
        self.TableWithBulkUpsert.BLOCK_SIZE = block_size

        self.TableWithBulkUpsert.bulk_upsert(
            db_session,
            [
                {"id": 1, "name": "update_old", "other": "post_1"},
                {"id": 3, "name": "create_with_id", "other": "post_3"},
                {"id": 4, "name": "over_block_size", "other": "post_4"},
            ],
        )

        rows = list(db_session.query(self.TableWithBulkUpsert))

        assert (
            rows
            == Any.iterable.containing(
                [
                    Any.instance_of(self.TableWithBulkUpsert).with_attrs(expected)
                    for expected in [
                        {"id": 1, "name": "update_old", "other": "pre_1"},
                        {"id": 2, "name": "pre_existing_2", "other": "pre_2"},
                        {"id": 3, "name": "create_with_id", "other": "post_3"},
                        {"id": 4, "name": "over_block_size", "other": "post_4"},
                    ]
                ]
            ).only()
        )

    def test_it_fails_with_badly_configured_host_class(self):
        class BadTable(BASE, BulkUpsertMixin):
            __tablename__ = "bad_table"
            id = sa.Column(sa.Integer, primary_key=True)

        with pytest.raises(NotImplementedError):
            BadTable.bulk_upsert(sentinel.session, [{}])
