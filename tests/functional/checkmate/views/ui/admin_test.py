import pytest

from tests.functional.matchers import temporary_redirect_to


class TestAdminPages:
    def test_if_youre_not_logged_in_it_redirects_to_the_login_page(
        self, app, route_url
    ):
        response = app.get("/ui/admin")

        assert response == temporary_redirect_to(route_url("login"))

    @pytest.mark.usefixtures("logged_in")
    def test_if_you_are_logged_in_it_passes_your_cookie_to_the_template(
        self, app, route_url
    ):
        response = app.get("/ui/admin", status=200)

        assert response.content_type == "text/html"
        assert app.cookies["session"].encode() in response.body


class TestAdminLoginFailure:
    def test_it(self, app):
        app.get("/ui/admin/login_failure", status=401)
