from unittest.mock import sentinel

from pyramid.events import NewRequest

from checkmate.subscribers import set_public_server_name


class TestSubscribers:
    def test_set_public_server_name(self, pyramid_request):
        pyramid_request.registry.settings["public_host"] = sentinel.public_host
        pyramid_request.registry.settings["public_scheme"] = sentinel.public_scheme
        event = NewRequest(pyramid_request)

        set_public_server_name(event)

        assert event.request.environ["HTTP_HOST"] == sentinel.public_host
        assert event.request.environ["wsgi.url_scheme"] == sentinel.public_scheme
