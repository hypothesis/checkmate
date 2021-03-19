# pylint: disable=no-self-use
"""A place to put fixture functions that are useful application-wide."""
from unittest.mock import MagicMock
from urllib.parse import urlencode

import httpretty
import sqlalchemy
from pyramid import testing
from pyramid.request import Request, apply_request_extensions
from pyramid.testing import DummySession
from sqlalchemy.orm import sessionmaker

from checkmate.routes import add_routes
from tests import factories
from tests.unit.services import *  # pylint: disable=wildcard-import,unused-wildcard-import


@pytest.fixture
def pyramid_config(pyramid_settings):
    with testing.testConfig(settings=pyramid_settings) as config:
        config.include("pyramid_services")
        add_routes(config)
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


@pytest.fixture
def session(pyramid_request):
    session = DummySession()
    pyramid_request.session = session
    return session


def _make_request(path, pyramid_config, db_session):
    pyramid_request = Request.blank(path)
    pyramid_request.registry = pyramid_config.registry
    pyramid_request.tm = MagicMock()
    pyramid_request.db = db_session

    apply_request_extensions(pyramid_request)

    return pyramid_request


SESSION_MAKER = sessionmaker()


@pytest.fixture
def db_session(db_engine):
    """Get a standalone database session for preparing database state."""

    conn = db_engine.connect()
    trans = conn.begin()
    session = SESSION_MAKER(bind=conn)
    session.begin_nested()  # pylint:disable=no-member

    @sqlalchemy.event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):  # pylint:disable=unused-variable
        if (
            transaction.nested
            and not transaction._parent.nested  # pylint: disable=protected-access
        ):
            session.begin_nested()

    factories.set_sqlalchemy_session(session, persistence="commit")

    try:
        yield session
    finally:
        factories.clear_sqlalchemy_session()
        session.close()  # pylint:disable=no-member
        trans.rollback()
        conn.close()


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
