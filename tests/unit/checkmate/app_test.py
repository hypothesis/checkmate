from unittest.mock import call

import pytest

from checkmate.app import load_settings

REQUIRED_PARAMS = ["database_url", "checkmate_blocklist_path"]


class TestLoadSettings:
    @pytest.mark.parametrize("param", REQUIRED_PARAMS)
    def test_it_reads_from_inputs(self, param):
        settings = load_settings({param: "value"})

        assert settings[param] == "value"

    @pytest.mark.parametrize("param", REQUIRED_PARAMS)
    def test_it_reads_parameters_from_the_os_environ(self, param, os):
        settings = load_settings({})

        assert call(param.upper()) in os.environ.get.mock_calls
        assert settings[param] == os.environ.get.return_value

    @pytest.mark.parametrize("param", REQUIRED_PARAMS)
    def test_it_crashes_without_a_required_param(self, param):
        with pytest.raises(ValueError):
            load_settings({param: None})

    @pytest.mark.parametrize("param", REQUIRED_PARAMS + ["checkmate_blocklist_url"])
    def test_it_crashes_without_a_required_param_as_celery_worker(self, param):
        with pytest.raises(ValueError):
            load_settings({param: None}, celery_worker=True)

    def test_it_can_configure_for_celery_workers(self):
        settings = load_settings({}, celery_worker=True)

        assert settings["h_pyramid_sentry.celery_support"]

    @pytest.fixture(autouse=True)
    def os(self, patch):
        return patch("checkmate.app.os")
