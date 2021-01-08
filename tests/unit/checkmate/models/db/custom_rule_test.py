import pytest

from checkmate.models import Reason
from tests import factories


@pytest.mark.usefixtures("db_session")
class TestCustomRule:
    def test_reasons(self):
        reasons = [Reason.HIGH_IO, Reason.MEDIA_IMAGE]

        rule = factories.CustomRule(tags=[reason.value for reason in reasons])

        assert rule.reasons == reasons
