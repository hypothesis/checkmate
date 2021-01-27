from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.urldispatch import Route

from checkmate.services.secure_link import SecureLinkService, factory


class TestSecureLinkService:
    def test_route_url_works(self, service, signature_service):
        signature_service.sign_items.return_value = "secure_token"
        query = {"param_1": "value_1", "param_2": "value_2"}
        result = service.route_url("present_block", _query=query)

        signature_service.sign_items.assert_called_once_with(
            [
                "present_block",
                "param_1",
                "value_1",
                "param_2",
                "value_2",
                service.VERSION_ARG,
                "1",
            ]
        )

        assert result == Any.url.with_query(
            dict(query, **{service.VERSION_ARG: "1", service.TOKEN_ARG: "secure_token"})
        )

    def test_route_url_requires_a_query(self, service):
        with pytest.raises(ValueError):
            service.route_url("present_block", _query=None)

    def test_is_secure_allows_a_signed_value(
        self, service, pyramid_request, signature_service
    ):
        pyramid_request.GET.update(
            {
                service.TOKEN_ARG: "expected_token",
                service.VERSION_ARG: "1",
                "other": "value",
            }
        )

        signature_service.sign_items.return_value = "expected_token"

        assert service.is_secure(pyramid_request)

        signature_service.sign_items.assert_called_once_with(
            [
                pyramid_request.matched_route.name,
                "other",
                "value",
                service.VERSION_ARG,
                "1",
            ]
        )

    def test_is_secure_disallows_different_tokens(
        self, service, pyramid_request, signature_service
    ):
        pyramid_request.GET.update(
            {service.TOKEN_ARG: "unexpected_token", service.VERSION_ARG: "1"}
        )

        signature_service.sign_items.return_value = "expected_token"

        assert not service.is_secure(pyramid_request)

    def test_is_secure_checks_for_missing_version(self, service, pyramid_request):
        pyramid_request.GET.update(
            {
                service.TOKEN_ARG: "unexpected_token",
                # service.VERSION_ARG: "1",
            }
        )

        assert not service.is_secure(pyramid_request)

    def test_is_secure_checks_for_missing_token(self, service, pyramid_request):
        pyramid_request.GET.update(
            {
                # service.TOKEN_ARG: "unexpected_token",
                service.VERSION_ARG: "1",
            }
        )

        assert not service.is_secure(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matched_route = Route("present_block", "/ui/block")

        return pyramid_request

    @pytest.fixture
    def service(self, pyramid_request, signature_service):
        return SecureLinkService(
            signature_service=signature_service, route_url=pyramid_request.route_url
        )


class TestFactory:
    def test_it(self, pyramid_request, signature_service):
        pyramid_request.registry.settings[
            "checkmate_secret"
        ] = sentinel.checkmate_secret

        service = factory(sentinel.context, pyramid_request)

        assert isinstance(service, SecureLinkService)
        # pylint: disable=protected-access
        assert service._signature_service == signature_service
        assert service._route_url == pyramid_request.route_url
