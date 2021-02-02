from unittest.mock import sentinel

import pytest

from checkmate.models.principals import Principals


class TestPrincipals:
    @pytest.mark.parametrize(
        "user_id,principals",
        (
            ("any_user@hypothes.is", (Principals.STAFF,)),
            ("some_random@gmail.com", None),
            ("arbitrary_string", None),
        ),
    )
    def test_from_user_id(self, user_id, principals):
        assert Principals.from_user_id(user_id, sentinel.request) == principals
