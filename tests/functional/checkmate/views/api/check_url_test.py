import webtest
from h_matchers import Any

from checkmate.app import create_app


class TestAPIAuth:
    def test_403_forbidden(self, app):
        res = app.get("/api/check", expect_errors=True)

        assert res.status_code == 403

    def test_403_forbidden_no_matching_users(self, app):
        app.authorization = ("Basic", ("api_nonsense",))

        res = app.get("/api/check", expect_errors=True)

        assert res.status_code == 403

    def test_authenticated_existing_user(self, app):
        checked_url = "http://example.com"
        app.authorization = ("Basic", ("dev_api_key", ""))

        res = app.get(
            "/api/check",
            {"url": checked_url},
        )

        assert res.status_code == 200
        assert res.json["data"][0]["id"] == "not-explicitly-allowed"
        assert res.json["links"]["html"] == Any.url.with_query(
            {
                "url": checked_url,
                "reason": "not-explicitly-allowed",
                "v": "1",
                "sec": Any.string(),
            }
        )

    def test_authenticated_existing_user_public_url(self, pyramid_settings, db_engine):

        checked_url = "http://example.com"
        settings = dict(pyramid_settings)
        settings["public_host"] = "public.checkmate.com"
        settings["public_scheme"] = "https"

        app = webtest.TestApp(create_app(None, **settings))
        app.authorization = ("Basic", ("dev_api_key", ""))

        res = app.get(
            "/api/check",
            {"url": checked_url},
        )

        assert res.status_code == 200
        assert res.json["links"]["html"] == Any.url(
            scheme="https", host="public.checkmate.com"
        ).with_query(
            {
                "url": checked_url,
                "reason": "not-explicitly-allowed",
                "v": "1",
                "sec": Any.string(),
            }
        )
