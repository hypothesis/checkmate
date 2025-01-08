from contextlib import contextmanager

import pytest

from checkmate.app import CheckmateConfigurator
from checkmate.celery_async.tasks import initialize_urlhaus, sync_urlhaus


@pytest.mark.usefixtures("URLHaus")
class TestInitializeURLHaus:
    def test_it(self, pyramid_request, URLHaus):
        initialize_urlhaus()

        URLHaus.assert_called_once_with(pyramid_request.db)
        URLHaus.return_value.reinitialize_db.assert_called_once_with()


@pytest.mark.usefixtures("URLHaus")
class TestSyncURLHaus:
    def test_it(self, pyramid_request, URLHaus):
        sync_urlhaus()

        URLHaus.assert_called_once_with(pyramid_request.db)
        URLHaus.return_value.update_db.assert_called_once_with()


@pytest.fixture
def pyramid_config(pyramid_config):
    CheckmateConfigurator(pyramid_config, celery_worker=True)

    return pyramid_config


@pytest.fixture()
def URLHaus(patch):
    return patch("checkmate.celery_async.tasks.URLHaus")


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("checkmate.celery_async.tasks.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
