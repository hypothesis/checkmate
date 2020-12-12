from contextlib import contextmanager
from unittest.mock import sentinel

import pytest
from requests import RequestException

from checkmate.app import configure
from checkmate.async.tasks import initialize_urlhaus, sync_blocklist, sync_urlhaus


@pytest.mark.usefixtures("CustomRules")
class TestSyncBlocklist:
    def test_it_works_with_url(self, CustomRules, pyramid_request):
        pyramid_request.registry.settings["checkmate_blocklist_url"] = sentinel.url

        sync_blocklist()

        CustomRules.assert_called_once_with(pyramid_request.db)
        CustomRules.return_value.load_simple_rule_url.assert_called_once_with(
            sentinel.url
        )

    def test_it_does_nothing_without_url(self, CustomRules, pyramid_request):
        pyramid_request.registry.settings["checkmate_blocklist_url"] = None

        sync_blocklist()

        CustomRules.assert_not_called()

    def test_it_handles_request_exceptions(self, CustomRules, pyramid_request):
        pyramid_request.registry.settings["checkmate_blocklist_url"] = sentinel.url

        CustomRules.return_value.load_simple_rule_url.side_effect = RequestException

        sync_blocklist()

        # Nothing really happens, we just carry on


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
    configure(pyramid_config, celery_worker=True)

    return pyramid_config


@pytest.fixture()
def CustomRules(patch):
    return patch("checkmate.async.tasks.CustomRules")


@pytest.fixture()
def URLHaus(patch):
    return patch("checkmate.async.tasks.URLHaus")


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("checkmate.async.tasks.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
