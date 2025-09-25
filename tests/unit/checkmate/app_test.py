from unittest.mock import ANY, call, create_autospec, sentinel

import pytest
from pyramid.config import Configurator

from checkmate.app import CheckmateConfigurator, sentry_before_send_log

CELERY_SETTINGS = {
    "database_url": "celery_db",
}

REQUIRED_APP_SETTINGS = {
    "database_url": "app_db",
    "checkmate_secret": "not_a_secret",
    "public_host": "localhost",
}

OPTIONAL_APP_SETTINGS = {
    "public_scheme": "localhost",
    "public_port": "9099",
}

DIFFERENT_ENVVAR_NAME_APP_SETTINGS = {
    "pyramid_googleauth.secret": "not_a_secret",
    "pyramid_googleauth.google_client_id": "some_long_hex_string",
    "pyramid_googleauth.google_client_secret": "another_not_secret",
}


APP_SETTINGS = {
    **REQUIRED_APP_SETTINGS,
    **OPTIONAL_APP_SETTINGS,
    **DIFFERENT_ENVVAR_NAME_APP_SETTINGS,
}


class TestSentryBeforeSendLog:
    @pytest.mark.parametrize(
        "log,should_be_filtered_out",
        [
            ({"attributes": {"logger.name": "gunicorn.access"}}, True),
            ({"attributes": {"logger.name": "foo"}}, False),
            ({}, False),
        ],
    )
    def test_it(self, log, should_be_filtered_out):
        result = sentry_before_send_log(log, sentinel.hint)

        if should_be_filtered_out:
            assert result is None
        else:
            assert result == log


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
        config.registry.settings.update(DIFFERENT_ENVVAR_NAME_APP_SETTINGS)
        CheckmateConfigurator(config, celery_worker=False)

        config.add_settings.assert_has_calls([call({setting: ANY})])

    @pytest.mark.parametrize(
        "setting", ({**REQUIRED_APP_SETTINGS, **OPTIONAL_APP_SETTINGS}.keys())
    )
    def test_it_reads_from_os_same_name(self, config, setting, os):
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
    def test_it_sets_api_keys_blank_if_not_specified(self, config):
        config.registry.settings.update(APP_SETTINGS)

        CheckmateConfigurator(config)

        config.add_settings.assert_has_calls([call({"api_keys": {}})], any_order=True)

    def test_it_adds_api_keys_from_env(self, config, monkeypatch):
        config.registry.settings.update(APP_SETTINGS)
        monkeypatch.setenv("CHECKMATE_API_KEY_USER_1", "api-key")

        CheckmateConfigurator(config)

        config.add_settings.assert_has_calls(
            [call({"api_keys": {"api-key": "user_1"}})], any_order=True
        )

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
