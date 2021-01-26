from unittest.mock import call, create_autospec

import pytest
from pyramid.config import Configurator

from checkmate.app import CheckmateConfigurator

CELERY_SETTINGS = {"database_url": "celery_db", "checkmate_blocklist_url": "some_url"}
APP_SETTINGS = {"database_url": "app_db", "checkmate_secret": "not_a_secret"}


class TestCheckmateConfigurator:
    def test_it_loads_for_the_app(self, config):
        config.registry.settings.update(APP_SETTINGS)

        CheckmateConfigurator(config, celery_worker=False)

        config.include.assert_has_calls(
            [
                call("checkmate.routes"),
                call("checkmate.models"),
                call("checkmate.db"),
                call("checkmate.services"),
                call("pyramid_exclog"),
                call("pyramid_jinja2"),
                call("h_pyramid_sentry"),
                call("pyramid_services"),
                call("pyramid_sanity"),
                call("pyramid_tm"),
            ],
            any_order=True,
        )

        config.scan.assert_has_calls([call("checkmate.views")])

    @pytest.mark.parametrize("setting", list(APP_SETTINGS.keys()))
    def test_it_notices_missing_app_settings(self, config, setting):
        config.registry.settings.update(APP_SETTINGS)
        config.registry.settings.pop(setting)

        with pytest.raises(ValueError):
            CheckmateConfigurator(config, celery_worker=False)

    @pytest.mark.parametrize("setting", (APP_SETTINGS.keys()))
    def test_it_reads_from_os(self, config, setting, os):
        config.registry.settings.update(APP_SETTINGS)
        config.registry.settings.pop(setting)

        CheckmateConfigurator(config, celery_worker=False)

        os.environ.get.assert_called_once_with(setting.upper())
        config.add_settings.assert_has_calls(
            [call({setting: os.environ.get.return_value})]
        )

    def test_it_loads_for_celery(self, config):
        config.registry.settings.update(CELERY_SETTINGS)

        CheckmateConfigurator(config, celery_worker=True)

        config.include.assert_has_calls(
            [
                call("checkmate.models"),
                call("checkmate.db"),
                call("h_pyramid_sentry"),
                call("pyramid_exclog"),
                call("pyramid_tm"),
                call("pyramid_sanity"),
            ],
            any_order=True,
        )

        config.scan.assert_not_called()

    @pytest.mark.parametrize("setting", list(CELERY_SETTINGS.keys()))
    def test_it_notices_missing_celery_settings(self, config, setting):
        config.registry.settings.update(CELERY_SETTINGS)
        config.registry.settings.pop(setting)

        with pytest.raises(ValueError):
            CheckmateConfigurator(config, celery_worker=True)

    @pytest.fixture
    def config(self):
        config = create_autospec(Configurator(), spec_set=True)
        config.registry.settings = {}
        return config

    @pytest.fixture
    def os(self, patch):
        return patch("checkmate.app.os")
