import pytest


class TestAddToAllowList:
    def test_a_request_with_no_auth_is_not_authenticated(self, app, json_body):
        app.post_json("/api/rule", json_body, status=403)

    def test_a_request_with_http_basic_auth_is_not_authenticated(self, app, json_body):
        app.authorization = ("Basic", ("dev_api_key", ""))

        app.post_json("/api/rule", json_body, status=403)

    @pytest.mark.usefixtures("logged_in")
    def test_a_request_with_a_session_cookie_succeeds(self, app, json_body):
        response = app.post_json("/api/rule", json_body, status=201)

        assert response.json == {
            "data": {
                "attributes": {
                    "force": False,
                    "hash": "73d986e009065f182c10bcb6a45db3d6eda9498f8930654af2653f8a938cd801",
                    "rule": "example.com/",
                    "tags": ["manual"],
                },
                "id": 1,
                "type": "AllowRule",
            }
        }

    @pytest.fixture
    def json_body(self):
        """Return a valid JSON body for POSTing to the API."""
        return {
            "data": {
                "type": "AllowRule",
                "attributes": {"url": "http://example.com"},
            }
        }
