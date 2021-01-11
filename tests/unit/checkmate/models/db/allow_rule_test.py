import pytest
from sqlalchemy.exc import IntegrityError

from checkmate.models import AllowRule


class TestAllowRule:
    def test_you_cant_make_an_AllowRule_with_no_tags(self, db_session):
        db_session.add(AllowRule(hash="foo", rule="bar", tags=[]))

        with pytest.raises(IntegrityError, match="ck__allow_rule__tags_cardinality"):
            db_session.flush()
