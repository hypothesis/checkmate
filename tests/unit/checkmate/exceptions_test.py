from checkmate.exceptions import BadURLParameter, JSONAPIException


class TestJSONAPIException:
    def test_it(self):
        error = JSONAPIException("message")

        assert error.normalized_messages() == {
            "errors": [{"detail": "message", "id": "JSONAPIException"}]
        }


class TestBadURLParameter:
    def test_it(self):
        error = BadURLParameter("param_name", "Bad param")

        assert error.normalized_messages() == {
            "errors": [
                {
                    "detail": "Bad param",
                    "id": "BadURLParameter",
                    "source": {"parameter": "param_name"},
                }
            ]
        }
