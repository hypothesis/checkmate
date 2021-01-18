from unittest import mock

import pytest

from checkmate.services import URLCheckerService
from checkmate.services.secure_link import SecureLinkService


@pytest.fixture
def mock_service(pyramid_config):
    def mock_service(service_class):
        mock_service = mock.create_autospec(service_class, spec_set=True, instance=True)
        pyramid_config.register_service(mock_service, iface=service_class)

        return mock_service

    return mock_service


@pytest.fixture
def secure_link_service(mock_service):
    return mock_service(SecureLinkService)


@pytest.fixture
def url_checker_service(mock_service):
    return mock_service(URLCheckerService)
