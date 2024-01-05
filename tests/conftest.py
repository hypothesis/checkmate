import functools
from os import environ
from unittest import mock

import httpretty
import pytest
from pyramid.testing import DummyRequest, testConfig
from sqlalchemy.orm import sessionmaker

from checkmate.db import create_engine
from tests import factories


@pytest.fixture(scope="session")
def db_engine():
    return create_engine(environ["DATABASE_URL"])


@pytest.fixture(scope="session")
def db_sessionfactory():
    return sessionmaker()


@pytest.fixture
def db_session(db_engine, db_sessionfactory):
    """Return the SQLAlchemy database session.

    This returns a session that is wrapped in an external transaction that is
    rolled back after each test, so tests can't make database changes that
    affect later tests.  Even if the test (or the code under test) calls
    session.commit() this won't touch the external transaction.

    This is the same technique as used in SQLAlchemy's own CI:
    https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = db_sessionfactory(
        bind=connection, join_transaction_mode="create_savepoint"
    )
    factories.set_sqlalchemy_session(session, persistence="commit")

    yield session

    factories.clear_sqlalchemy_session()
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def pyramid_settings():
    return {
        "database_url": environ["DATABASE_URL"],
        "checkmate_secret": environ.get("CHECKMATE_SECRET", "not-very-secret"),
        "api_keys": {"dev_api_key": "dev"},
        "pyramid_googleauth.secret": environ.get("CHECKMATE_SECRET", "not-very-secret"),
        "pyramid_googleauth.google_client_id": "google_client_id",
        "pyramid_googleauth.google_client_secret": "google_client_secret",
        "public_host": "localhost",
        "public_scheme": "http",
        "public_port": "9099",
    }


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


@pytest.fixture
def route_url(pyramid_settings):
    request = DummyRequest(environ={"SERVER_NAME": "localhost"})

    with testConfig(request=request, settings=pyramid_settings) as config:
        config.include("pyramid_services")
        config.include("checkmate.routes")
        config.include("pyramid_googleauth")

        yield functools.partial(request.route_url, _scheme="https")


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
