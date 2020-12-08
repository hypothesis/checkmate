from celery import Celery

from checkmate.async.celery import app


class TestApp:
    def test_sanity(self):
        assert isinstance(app, Celery)
