# pylint: disable=no-self-use
"""A place to put fixture functions that are useful application-wide."""
import functools
import os
from unittest import mock
from unittest.mock import MagicMock
from urllib.parse import urlencode

import httpretty
import pytest
from pyramid import testing
from pyramid.request import Request
from sqlalchemy.orm import sessionmaker

from checkmate.db import create_engine
from tests import factories


def autopatcher(request, target, **kwargs):
    """Patch and cleanup automatically. Wraps :py:func:`mock.patch`."""
    options = {"autospec": True}
    options.update(kwargs)
    patcher = mock.patch(target, **options)
    obj = patcher.start()
    request.addfinalizer(patcher.stop)
    return obj


@pytest.fixture
def patch(request):
    return functools.partial(autopatcher, request)


@pytest.fixture(scope="session")
def pyramid_settings():
    return {
        "database_url": os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql://postgres@localhost:5434/checkmate_test",
        )
    }


@pytest.fixture
def pyramid_config(pyramid_settings):
    with testing.testConfig(settings=pyramid_settings) as config:
        yield config


@pytest.fixture
def pyramid_request(pyramid_config, db_session):
    return _make_request("/dummy", pyramid_config, db_session)


@pytest.fixture
def make_request(pyramid_config, db_session):
    def make_request(path="/irrelevant", params=None):
        if params:  # pragma: no cover
            path += "?" + urlencode(params)

        return _make_request(path, pyramid_config, db_session)

    return make_request


def _make_request(path, pyramid_config, db_session):
    pyramid_request = Request.blank(path)
    pyramid_request.registry = pyramid_config.registry
    pyramid_request.tm = MagicMock()
    pyramid_request.db = db_session

    return pyramid_request


@pytest.fixture(scope="session")
def db_engine(pyramid_settings):
    # Delete all database tables and re-initialize the database schema based on
    # the current models. Doing this at the beginning of each test run ensures
    # that any schema changes made to the models since the last test run will
    # be applied to the test DB schema before running the tests again.
    return create_engine(pyramid_settings["database_url"], drop=True)


SESSION_MAKER = sessionmaker()


@pytest.fixture
def db_session(db_engine):
    """Get a standalone database session for preparing database state."""

    conn = db_engine.connect()
    session = SESSION_MAKER(bind=conn)

    factories.set_sqlalchemy_session(session, persistence="commit")

    try:
        yield session
    finally:
        factories.clear_sqlalchemy_session()
        session.close()  # pylint:disable=no-member


@pytest.fixture(autouse=True)
def httpretty_():
    """Monkey-patch Python's socket core module to mock all HTTP responses.

    We never want real HTTP requests to be sent by the tests so replace them
    all with mock responses. This handles requests sent using the standard
    urllib2 library and the third-party httplib2 and requests libraries.
    """
    httpretty.enable(allow_net_connect=False)

    yield

    httpretty.disable()
    httpretty.reset()
