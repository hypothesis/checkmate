"""Fixtures that return real instances of the services.

Sometimes a test needs an instance of a service in order to create some value
or state that's needed for the test set up.

These fixtures create their own instances of the services that are separate
from the instances that the app itself will be using.
"""

import pytest

from checkmate.services import SignatureService


@pytest.fixture
def signature_service(pyramid_settings):
    return SignatureService(pyramid_settings["checkmate_secret"])
