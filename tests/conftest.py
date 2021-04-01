import functools
import os
from unittest import mock

import httpretty
import pytest
from pyramid.testing import DummyRequest, testConfig

from checkmate.db import create_engine

_TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://postgres@localhost:5434/checkmate_test",
)


@pytest.fixture(scope="session")
def db_engine():
    # Delete all database tables and re-initialize the database schema based on
    # the current models. Doing this at the beginning of each test run ensures
    # that any schema changes made to the models since the last test run will
    # be applied to the test DB schema before running the tests again.
    return create_engine(_TEST_DATABASE_URL, drop=True, max_overflow=15)


@pytest.fixture
def pyramid_settings():
    return {
        "database_url": _TEST_DATABASE_URL,
        "checkmate_secret": os.environ.get("CHECKMATE_SECRET", "not-very-secret"),
        "google_client_id": "google_client_id",
        "google_client_secret": "google_client_secret",
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
def route_url():
    request = DummyRequest(environ={"SERVER_NAME": "localhost"})

    with testConfig(request=request) as config:
        config.include("checkmate.routes")
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
