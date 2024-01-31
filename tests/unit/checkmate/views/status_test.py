import pytest
from h_matchers import Any

from checkmate.views.status import status


class TestStatusRoute:
    def test_it(self, pyramid_request, capture_message):
        assert status(pyramid_request) == Any.dict()
        capture_message.assert_not_called()

    def test_it_sends_test_messages_to_sentry(self, pyramid_request, capture_message):
        pyramid_request.params["sentry"] = ""

        status(pyramid_request)

        capture_message.assert_called_once_with(
            "Test message from Checkmate's status view"
        )


@pytest.fixture(autouse=True)
def capture_message(patch):
    return patch("checkmate.views.status.capture_message")
