from unittest.mock import ANY, call, create_autospec

import pytest
from pyramid.config import Configurator

from checkmate.app import CheckmateConfigurator

CELERY_SETTINGS = {
    "database_url": "celery_db",
    "checkmate_blocklist_url": "some_url",
}

REQUIRED_APP_SETTINGS = {
    "database_url": "app_db",
    "checkmate_secret": "not_a_secret",
    "google_client_id": "some_long_hex_string",
    "google_client_secret": "another_not_secret",
    "public_host": "localhost",
}

OPTIONAL_APP_SETTINGS = {
    "public_scheme": "localhost",
    "public_port": "9099",
}

APP_SETTINGS = {**REQUIRED_APP_SETTINGS, **OPTIONAL_APP_SETTINGS}


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

    @pytest.mark.usefixtures("with_clear_environ")
    @pytest.mark.parametrize("setting", list(REQUIRED_APP_SETTINGS.keys()))
    def test_it_notices_missing_app_settings(self, config, setting):
        config.registry.settings.update(REQUIRED_APP_SETTINGS)
        config.registry.settings.pop(setting)

        with pytest.raises(ValueError):
            CheckmateConfigurator(config, celery_worker=False)

    @pytest.mark.usefixtures("with_clear_environ")
    @pytest.mark.parametrize("setting", list(OPTIONAL_APP_SETTINGS.keys()))
    def test_takes_default_value_setting(self, config, setting):
        config.registry.settings.update(REQUIRED_APP_SETTINGS)
        CheckmateConfigurator(config, celery_worker=False)

        config.add_settings.assert_has_calls([call({setting: ANY})])

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

    @pytest.mark.usefixtures("with_clear_environ")
    def test_load_api_keys_empty(self, config):
        # pylint: disable=protected-access
        api_keys = CheckmateConfigurator._get_api_keys_from_env()
        assert list(api_keys) == []

    def test_load_api_keys(self, monkeypatch):
        # pylint: disable=protected-access
        monkeypatch.setenv("CHECKMATE_API_KEY_USER_1", "api-key")
        api_keys = CheckmateConfigurator._get_api_keys_from_env()

        assert list(api_keys) == [("api-key", "user_1")]

    @pytest.mark.usefixtures("with_clear_environ")
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
    def with_clear_environ(self, os):
        os.environ.get.return_value = None

    @pytest.fixture
    def os(self, patch):
        return patch("checkmate.app.os")
