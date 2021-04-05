# pylint: disable=no-self-use
"""A place to put fixture functions that are useful application-wide."""
import json

import sqlalchemy
from pyramid import testing
from pyramid.request import apply_request_extensions
from pyramid.testing import DummyRequest
from sqlalchemy.orm import sessionmaker

from checkmate.routes import add_routes
from tests import factories
from tests.unit.services import *  # pylint: disable=wildcard-import,unused-wildcard-import


@pytest.fixture
def pyramid_config(pyramid_settings):
    with testing.testConfig(settings=pyramid_settings) as config:
        config.include("pyramid_services")
        config.include("pyramid_tm")

        add_routes(config)

        yield config


class EnhancedDummyRequest(DummyRequest):  # pylint:disable=too-many-ancestors
    """A subclass that adds some missing features to DummyRequest.

    Real Request objects have a `json_body` property and a `json` property
    that's an alias for `json_body`. DummyRequest is missing both.
    EnhancedDummyRequest adds the missing `json` and `json_body` properties.

    By default reading `json` or `json_body` will raise JSONDecodeError, which
    is what reading a real Request's `json` or `json_body` does if the request
    doesn't have a JSON body.

    Tests can set pyramid_request.body to a JSON string, then reading `json` or
    `json_body` will return json.loads(body).
    """

    @property
    def json_body(self):
        return json.loads(self.body)

    @property
    def json(self):
        return self.json_body


@pytest.fixture
def pyramid_request(
    db_session,
    pyramid_config,  # pylint:disable=unused-argument
):
    pyramid_request = EnhancedDummyRequest(
        db=db_session, environ={"HTTP_HOST": "example.com"}
    )
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
