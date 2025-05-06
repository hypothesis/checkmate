import pytest
from webtest import TestApp

from checkmate.app import create_app


def test_index(app):
    response = app.get("/")

    assert response.text == "Hello world!"


def test_status(app):
    response = app.get("/_status")

    assert response.json == {"status": "okay"}


@pytest.fixture
def app():
    return TestApp(create_app({}))
