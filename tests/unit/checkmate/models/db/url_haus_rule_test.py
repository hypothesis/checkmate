from checkmate.models import URLHausRule


class TestURLHausRule:
    def test_truncate(self, db_session):
        db_session.add(URLHausRule(id=1, hash="hash", rule="http://example.com"))
        db_session.flush()
        assert db_session.query(URLHausRule).count() == 1

        URLHausRule.truncate(db_session)

        assert not db_session.query(URLHausRule).count()
