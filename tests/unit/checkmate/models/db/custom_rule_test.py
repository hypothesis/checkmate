import pytest

from checkmate.checker.url.reason import Reason
from checkmate.models.db.custom_rule import CustomRule
from tests import factories


@pytest.mark.usefixtures("db_session")
class TestCustomRule:
    def test_it_matches(self, db_session):
        hit = factories.CustomRule()
        _noise = factories.CustomRule()

        hits = CustomRule.find_matches(db_session, [hit.hash, "non_matching_hash"])

        assert list(hits) == [hit]

    def test_reasons(self):
        reasons = [Reason.HIGH_IO, Reason.MEDIA_IMAGE]

        rule = factories.CustomRule(tags=[reason.value for reason in reasons])

        assert rule.reasons == reasons
