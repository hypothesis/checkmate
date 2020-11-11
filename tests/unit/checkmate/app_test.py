from unittest.mock import call

import pytest

from checkmate.app import REQUIRED_PARAMS, load_settings


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
    def test_it_crashes_without_a_required_param(self, param, os):
        with pytest.raises(ValueError):
            load_settings({param: None})

    @pytest.fixture(autouse=True)
    def os(self, patch):
        return patch("checkmate.app.os")
