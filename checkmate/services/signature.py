"""Create secure hashes."""

import random
from hashlib import sha256


class SignatureService:
    """A class for signing things and checking the signatures."""

    HEX_DIGITS = "012345678abcdef"
    SALT_LENGTH = 32

    def __init__(self, secret):
        """Return a new SignatureService object.

        :param secret: The secret to sign and check args with
        """
        self._secret = secret

    def get_nonce(self):
        """Create a random verifiable nonce value."""

        salt = "".join(random.choices(self.HEX_DIGITS, k=self.SALT_LENGTH))
        signature = self.sign_items([salt])

        return salt + signature

    def check_nonce(self, nonce):
        """Check a nonce was created with `get_nonce`.

        :param nonce: String to check
        :return: Boolean indicating if this is a valid nonce
        """

        salt, signature = nonce[: self.SALT_LENGTH], nonce[self.SALT_LENGTH :]

        return signature == self.sign_items([salt])

    def sign_items(self, items):
        """Hash any list of "stringable" things."""
        digest = sha256()

        # Add our secret to every hash
        digest.update(self._secret.encode("utf-8"))

        for item in items:
            digest.update(str(item).encode("utf-8"))

        return digest.hexdigest()
