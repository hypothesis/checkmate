from checkmate.exceptions import BadURLParameter, JSONAPIException


class TestJSONAPIException:
    def test_it(self):
        error = JSONAPIException("message")

        assert error.serialise() == {"detail": "message", "id": "JSONAPIException"}


class TestBadURLParameter:
    def test_it(self):
        error = BadURLParameter("param_name", "Bad param")

        assert error.serialise() == {
            "detail": "Bad param",
            "id": "BadURLParameter",
            "source": {"parameter": "param_name"},
        }
