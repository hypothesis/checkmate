from contextlib import contextmanager
from unittest.mock import sentinel

import pytest
from requests import RequestException

from checkmate.app import configure
from checkmate.async.tasks import sync_blocklist


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

    @pytest.fixture(autouse=True)
    def CustomRules(self, patch):
        return patch("checkmate.async.tasks.CustomRules")

    @pytest.fixture(autouse=True)
    def app(self, patch, pyramid_request):
        app = patch("checkmate.async.tasks.app")

        @contextmanager
        def request_context():
            yield pyramid_request

        app.request_context = request_context

        return app

    @pytest.fixture
    def pyramid_config(self, pyramid_config):
        configure(pyramid_config, celery_worker=True)

        return pyramid_config
