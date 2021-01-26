import contextlib

import pytest
from webtest import TestApp

from checkmate import db
from checkmate.app import create_app


@pytest.fixture(autouse=True)
def clean_database(db_engine):
    """Delete any data added by the previous test."""
    tables = reversed(db.BASE.metadata.sorted_tables)
    with contextlib.closing(db_engine.connect()) as conn:
        transaction = conn.begin()
        tnames = ", ".join('"' + t.name + '"' for t in tables)
        conn.execute("TRUNCATE {};".format(tnames))
        transaction.commit()


@pytest.fixture
def app(pyramid_app, db_engine):
    return TestApp(pyramid_app)


@pytest.fixture(scope="session")
def pyramid_app(pyramid_settings):
    return create_app(None, **pyramid_settings)
