class TestCheckUrl:
    def test_not_in_blocklist(self, app):
        res = app.get(
            "/api/check",
            {"url": "http://example.com"},
        )

        assert res.status_code == 200
        assert res.json["data"][0]["id"] == "not-explicitly-allowed"
