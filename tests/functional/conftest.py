import contextlib

import pytest
import sqlalchemy as sa
from webtest import TestApp

from checkmate import db
from checkmate.app import create_app
from tests.functional.mock_services import (  # pylint:disable=unused-import
    mock_google_auth_service,
)
from tests.functional.services import signature_service  # pylint:disable=unused-import


@pytest.fixture(autouse=True)
def clean_database(db_engine):
    """Delete any data added by the previous test."""
    tables = reversed(db.BASE.metadata.sorted_tables)
    with contextlib.closing(db_engine.connect()) as conn:
        transaction = conn.begin()
        tnames = ", ".join('"' + t.name + '"' for t in tables)
        conn.execute(sa.text(f"TRUNCATE {tnames};"))
        transaction.commit()


@pytest.fixture
def app(pyramid_app, db_engine):  # pylint:disable=unused-argument
    # This extra_environ is necessary to get webtest to use https and port
    # 443 when you give it a path rather than a full URL `app.get("/foo/bar")`.
    # We need it to use SSL because the admin pages use secure cookies
    return TestApp(
        pyramid_app,
        extra_environ={"wsgi.url_scheme": "https", "HTTP_HOST": "localhost:443"},
    )


@pytest.fixture
def logged_in(
    app,
    route_url,
    signature_service,
    mock_google_auth_service,  # pylint:disable=unused-argument
):
    """Make `app` be logged in to the admin pages with a session cookie."""
    # Google redirects the browser to our login callback URL with a state
    # param, and the login callback URL's response includes a session cookie in
    # a Set-Cookie header to log the browser in. Simulate that redirect
    # response so that the logged-in session cookie gets stored in
    # `app.cookiejar`. Webtest will automatically send the cookie in subsequent
    # requests made with `app`.
    app.get(
        route_url("pyramid_googleauth.login.callback"),
        params={"state": signature_service.get_nonce()},
    )


@pytest.fixture
def pyramid_app(pyramid_settings):
    return create_app(None, **pyramid_settings)
