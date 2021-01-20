from copy import deepcopy
from unittest.mock import create_autospec, sentinel

import pytest
from pyramid.urldispatch import Route

from checkmate.services.secure_link import SecureLinkService, factory

# pylint: disable=protected-access, too-many-arguments


class TestSecureLinkService:
    ROUTE_NAME = "my_view_name"

    def test_route_url_works(self, service, route, route_url, args, signed_args):
        result = service.route_url(route.name, _query=args)

        assert result == route_url.return_value

        route_url.assert_called_once_with(self.ROUTE_NAME, _query=signed_args)

    def test_route_url_requires_a_query(self, service):
        with pytest.raises(ValueError):
            service.route_url("irrelevant_route_name", _query=None)

    def test_is_secure_allows_a_signed_value(self, service, signed_request):
        assert service.is_secure(signed_request)

    @pytest.mark.parametrize("key", ("arg_1", "arg_2", "v", "sec"))
    @pytest.mark.parametrize("value", (None, "different"))
    def test_is_secure_detects_mutated_args(self, service, signed_request, key, value):
        if value:
            signed_request.GET[key] = value
        else:
            signed_request.GET.pop(key)

        before_call = deepcopy(dict(signed_request.GET))

        assert not service.is_secure(signed_request)

        # Check we don't mutate the args
        assert before_call == signed_request.GET

    def test_is_secure_detects_mismatched_route(self, service, signed_request):
        signed_request.matched_route.name = "something_wrong"

        assert not service.is_secure(signed_request)

    def test_is_secure_checks_for_missing_version(self, service, signed_request):
        signed_request.GET.pop(SecureLinkService.TOKEN_ARG)
        signed_request.GET.pop(SecureLinkService.VERSION_ARG)

        # These args are correctly signed, but don't have the version
        signed_request.GET[SecureLinkService.TOKEN_ARG] = service._hash_args(
            signed_request.matched_route.name, signed_request.GET
        )

        assert not service.is_secure(signed_request)

    def test_is_secure_detects_additional_args(self, service, signed_request):
        signed_request.GET["extra"] = "should not be here"

        assert not service.is_secure(signed_request)

    @pytest.fixture
    def route(self):
        return Route("my_view_name", "/some/url")

    @pytest.fixture
    def args(self):
        return {"arg_1": "some_value", "arg_2": "some_other_value"}

    @pytest.fixture
    def signed_args(self, args):
        signed_args = deepcopy(args)
        signed_args.update(
            {
                "v": "1",
                # This just happens to match the route name and args above
                "sec": "1706de1486ff38efdea4089ca29a6ca5de3affa7ba919138a5b184365559829a",
            }
        )
        return signed_args

    @pytest.fixture
    def signed_request(self, pyramid_request, signed_args, route):
        pyramid_request.GET.update(signed_args)
        pyramid_request.matched_route = route

        return pyramid_request

    @pytest.fixture
    def route_url(self, pyramid_request):
        return create_autospec(pyramid_request.route_url, spec_set=True)

    @pytest.fixture
    def service(self, route_url):
        return SecureLinkService(secret="not_very_secret", route_url=route_url)


class TestFactory:
    def test_it(self, pyramid_request):
        pyramid_request.registry.settings["secret"] = sentinel.secret

        service = factory(sentinel.context, pyramid_request)

        assert isinstance(service, SecureLinkService)
        assert service._secret == sentinel.secret
        assert service._route_url == pyramid_request.route_url
