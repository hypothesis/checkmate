import pytest
from h_matchers import Any

from checkmate.services.signature import SignatureService


class TestSignatureService:
    def test_sign_items(self, service):
        signature_1 = service.sign_items(["a", "b", "c"])
        signature_2 = service.sign_items(["a", "b", "c"])
        signature_3 = service.sign_items(["a", "b", "X"])

        assert signature_1 == signature_2
        assert signature_1 != signature_3
        # This protects against us accidentally changing how we hash
        assert (
            signature_1
            == "c5c325fe8a1f875a667eecc63d8beae83668f17cad4e05a3738c4e7e9e358652"
        )

    def test_get_nonce(self, service):
        # There's not much we can say about the nonce function without using
        # it in combination with check_nonce.

        nonce = service.get_nonce()
        assert len(nonce) == 64 + service.SALT_LENGTH
        assert nonce == Any.string.matching("^[a-z0-9]+$")

        # It's not just the same value over and over
        assert nonce != service.get_nonce()

    def test_check_nonce(self, service):
        # This is the main job, just to pass it's own check
        nonce = service.get_nonce()
        assert service.check_nonce(service.get_nonce())

        # Check it notices if we change one char
        last_char = "f" if nonce[-1] != "f" else "e"
        assert not service.check_nonce(nonce[:-1] + last_char)

    @pytest.fixture
    def service(self):
        return SignatureService(secret="not_very_secret")
