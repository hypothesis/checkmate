from h_matchers import Any

from checkmate.views.status import get_status


class TestStatusRoute:
    def test_status_returns_a_response(self, pyramid_request):
        assert get_status(pyramid_request) == Any.dict()
