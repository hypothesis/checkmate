from unittest.mock import sentinel

from pyramid.httpexceptions import HTTPFound

from checkmate.views.root import root


class TestRoot:
    def test_it_redirects_to_login(self, pyramid_request):
        response = root(sentinel.context, pyramid_request)

        assert isinstance(response, HTTPFound)
        assert response.location == "http://example.com/googleauth/login"
