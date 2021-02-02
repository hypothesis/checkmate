from enum import Enum


class Principals(Enum):
    """Security principals."""

    STAFF = "staff"

    @staticmethod
    def from_user_id(user_id, _request):
        """Convert from user ids to principals.

        This can be used as an authentication callback.
        """
        if user_id.endswith("@hypothes.is"):
            return (Principals.STAFF,)

        return None
