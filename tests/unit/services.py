from unittest import mock

import pytest

from checkmate.services import (
    GoogleAuthService,
    RuleService,
    SignatureService,
    URLCheckerService,
)
from checkmate.services.secure_link import SecureLinkService


@pytest.fixture
def mock_service(pyramid_config):
    def mock_service(service_class):
        mock_service = mock.create_autospec(service_class, spec_set=True, instance=True)
        pyramid_config.register_service(mock_service, iface=service_class)

        return mock_service

    return mock_service


@pytest.fixture
def signature_service(mock_service):
    signature_service = mock_service(SignatureService)
    signature_service.sign_items.return_value = "secure_token"
    return signature_service


@pytest.fixture
def secure_link_service(mock_service):
    return mock_service(SecureLinkService)


@pytest.fixture
def url_checker_service(mock_service):
    return mock_service(URLCheckerService)


@pytest.fixture
def google_auth_service(mock_service):
    return mock_service(GoogleAuthService)


@pytest.fixture
def rule_service(mock_service):
    return mock_service(RuleService)
