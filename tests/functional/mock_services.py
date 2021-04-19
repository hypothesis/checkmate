"""Fixtures that return mocks of the app's services.

These fixtures patch the service classes so the app itself will use the mock
versions of the services when the app is called via webtest.TestApp (the `app`
fixture) as long as the call to patch() happens before the request is sent to
the app.
"""

from unittest.mock import sentinel

import pytest


@pytest.fixture
def mock_google_auth_service(patch):
    MockGoogleAuthService = patch(
        "pyramid_googleauth.services.google_auth.GoogleAuthService"
    )
    mock_google_auth_service = MockGoogleAuthService.return_value
    mock_google_auth_service.exchange_auth_code.return_value = (
        {"email": "user@hypothes.is"},
        sentinel.credentials,
    )
    return mock_google_auth_service
