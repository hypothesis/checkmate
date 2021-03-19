import pytest


class TestAPIAuth:
    def test_no_secure_link(self, app):
        res = app.get("/ui/block?url=example.com", expect_errors=True)

        assert res.status_code == 403

    def test_not_explictly_allowed_block(self, secure_link, app):
        res = app.get(
            "/ui/block?url=example.com&reason=not-explicitly-allowed",
            expect_errors=True,
        )

        assert res.status_code == 403
        assert "Content cannot be annotated yet" in res.text

    @pytest.fixture
    def secure_link(self, patch):
        service = patch("checkmate.services.secure_link.SecureLinkService")
        service.is_secure.return_value = True
        return service
