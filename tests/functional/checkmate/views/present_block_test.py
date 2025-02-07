import pytest

from checkmate.services import SecureLinkService, SignatureService


class TestAPIAuth:
    def test_if_the_link_is_not_signed_it_401s(self, app):
        # `url` will be an unsigned link (it doesn't come from
        # SecureLinkService).
        app.get("/block", params={"url": "example.com"}, status=401)

    def test_if_the_link_is_signed_it_renders_the_block_page(
        self, app, secure_link_service
    ):
        url = secure_link_service.route_url(
            "present_block",
            _query={"url": "example.com", "reason": "not-explicitly-allowed"},
        )

        app.get(url, status=403)

    @pytest.fixture
    def secure_link_service(self, pyramid_settings, route_url):
        signature_service = SignatureService(pyramid_settings["checkmate_secret"])
        secure_link_service = SecureLinkService(signature_service, route_url)
        return secure_link_service
