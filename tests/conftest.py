import os

import pytest

from checkmate.db import create_engine


@pytest.fixture(scope="session")
def db_engine(pyramid_settings):
    # Delete all database tables and re-initialize the database schema based on
    # the current models. Doing this at the beginning of each test run ensures
    # that any schema changes made to the models since the last test run will
    # be applied to the test DB schema before running the tests again.
    return create_engine(pyramid_settings["database_url"], drop=True)


@pytest.fixture(scope="session")
def pyramid_settings():
    return {
        "database_url": os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql://postgres@localhost:5434/checkmate_test",
        ),
        "secret": os.environ.get("CHECKMATE_SECRET", "not-very-secret"),
        "google_client_id": "google_client_id",
        "google_client_secret": "google_client_secret",
    }
