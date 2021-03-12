"""Pyramid authentication-related models."""

from enum import Enum


class Principals(Enum):
    """Security principals."""

    STAFF = "staff"
    API = "api"

    @staticmethod
    def from_user_id(user_id, _request):
        """Convert from user ids to principals.

        This can be used as an authentication callback.
        """
        if user_id.endswith("@hypothes.is"):
            return (Principals.STAFF,)

        return None


class Permissions(Enum):
    """Security permissions."""

    CHECK_URL = "check_url"