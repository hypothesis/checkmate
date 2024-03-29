import functools
from os import environ
from unittest import mock

import httpretty
import pytest
from pyramid.testing import DummyRequest, testConfig


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
