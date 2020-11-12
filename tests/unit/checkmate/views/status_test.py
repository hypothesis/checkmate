from h_matchers import Any

from checkmate.views.status import get_status


class TestStatusRoute:
    def test_status_returns_a_response(self, make_request):
        request = make_request("/status")

        result = get_status(request)

        assert result == Any.dict()
