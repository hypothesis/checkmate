from h_matchers import Any

from checkmate.models import BlockedFor


class TestAPIAuth:
    def test_403_forbidden(self, app):
        app.get("/api/check", status=403)

    def test_403_forbidden_no_matching_users(self, app):
        app.authorization = ("Basic", ("api_nonsense",))

        app.get("/api/check", status=403)

    def test_authenticated_existing_user(self, app, pyramid_settings):
        checked_url = "http://example.com"
        app.authorization = ("Basic", ("dev_api_key", ""))

        res = app.get("/api/check", {"url": checked_url}, status=200)

        assert res.json["data"][0]["id"] == "not-explicitly-allowed"
        assert res.json["links"]["html"] == Any.url(
            scheme=pyramid_settings["public_scheme"],
            host=f"{pyramid_settings['public_host']}:{pyramid_settings['public_port']}",
        ).with_query(
            {
                "url": checked_url,
                "reason": "not-explicitly-allowed",
                "v": "1",
                "sec": Any.string(),
                "blocked_for": BlockedFor.GENERAL.value,
            }
        )
