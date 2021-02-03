class TestAPIAuth:
    def test_404_unauthenticated(self, app):
        res = app.get("/api/check", expect_errors=True)

        assert res.status_code == 401

    def test_404_unauthenticated_no_matching_users(self, app):
        app.authorization = ("Basic", ("api_nonsense",))
        res = app.get("/api/check", expect_errors=True)

        assert res.status_code == 401

    def test_authenticated_existing_user(self, app):
        app.authorization = ("Basic", ("not_api_key", ""))
        res = app.get(
            "/api/check",
            {"url": "http://example.com"},
        )

        assert res.status_code == 200
        assert res.json["data"][0]["id"] == "not-explicitly-allowed"
