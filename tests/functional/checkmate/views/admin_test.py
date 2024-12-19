import pytest

from tests.functional.matchers import temporary_redirect_to


class TestAdminLoginFailure:
    def test_it(self, app):
        app.get("/googleauth/login/failure", status=401)


class TestAdminAllowURL:
    def test_if_youre_not_logged_in_it_redirects_to_the_login_page(
        self, app, route_url
    ):
        response = app.get("/admin/allow_url/")

        assert response == temporary_redirect_to(route_url("pyramid_googleauth.login"))

    @pytest.mark.usefixtures("logged_in")
    def test_form_renders_correctly(self, app):
        response = app.get("/admin/allow_url/", status=200)

        assert response.content_type == "text/html"

    @pytest.mark.usefixtures("logged_in")
    def test_post_form_submission(self, app):
        response = app.post(
            "/admin/allow_url/", status=200, params={"url": "http://google.com"}
        )

        assert response.content_type == "text/html"
        assert "Allowed as google.com/" in response.text
