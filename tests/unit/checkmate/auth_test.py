from unittest.mock import call, create_autospec, sentinel

import pytest
from pyramid.authentication import (
    BasicAuthAuthenticationPolicy,
    RemoteUserAuthenticationPolicy,
    SessionAuthenticationPolicy,
)
from pyramid.security import Allowed, Authenticated, Denied, Everyone

from checkmate.auth import AuthorizationPolicy, CascadingAuthenticationPolicy
from checkmate.models import Permissions, Principals


class TestCascadingAuthenticationPolicy:
    def test_it_requires_some_policies(self):
        with pytest.raises(ValueError):
            CascadingAuthenticationPolicy([])

    def test_effective_policy_reads_the_first(
        self, policy, sub_policies, pyramid_request
    ):
        assert policy.effective_policy(pyramid_request) == sub_policies[0]

        sub_policies[0].authenticated_userid.assert_called_once_with(pyramid_request)
        sub_policies[1].authenticated_userid.assert_not_called()

    def test_effective_policy_cascades(self, policy, sub_policies, pyramid_request):
        sub_policies[0].authenticated_userid.return_value = None

        assert policy.effective_policy(pyramid_request) == sub_policies[1]

        sub_policies[0].authenticated_userid.assert_called_once_with(pyramid_request)
        sub_policies[1].authenticated_userid.assert_called_once_with(pyramid_request)

    def test_effective_policy_returns_the_last_if_none_apply(
        self, policy, sub_policies, pyramid_request
    ):
        sub_policies[0].authenticated_userid.return_value = None
        sub_policies[1].authenticated_userid.return_value = None

        assert policy.effective_policy(pyramid_request) == sub_policies[1]

    @pytest.mark.parametrize(
        "method,args",
        (
            ("authenticated_userid", ["request"]),
            ("unauthenticated_userid", ["request"]),
            ("effective_principals", ["request"]),
            ("forget", ["request"]),
        ),
    )
    def test_method_pass_through(self, method, args, policy):
        result = getattr(policy, method)(*args)

        # pylint: disable=protected-access
        # We should use effective_policy here, but it messes up the counts
        proxied_method = getattr(policy._sub_policies[0], method)
        assert result == proxied_method.return_value

        if method == "authenticated_userid":
            proxied_method.assert_has_calls([call(*args), call(*args)])
        else:
            proxied_method.assert_called_once_with(*args)

    @pytest.mark.parametrize("sub_policy_index", (0, 1))
    def test_remember_picks_a_policy(self, policy, sub_policy_index):
        # pylint: disable=protected-access
        sub_policy = policy._sub_policies[sub_policy_index]
        kwargs = {"a": 1, "b": 2}

        result = policy.remember(
            sentinel.request, sentinel.userid, iface=sub_policy.__class__, **kwargs
        )

        assert result == sub_policy.remember.return_value
        sub_policy.remember.assert_called_once_with(
            sentinel.request, sentinel.userid, **kwargs
        )

    @pytest.mark.parametrize(
        "iface,exception",
        (
            (None, TypeError),
            # Our setup doesn't have one of these and should raise
            (RemoteUserAuthenticationPolicy, KeyError),
        ),
    )
    def test_remember_raises_with_bad_policy_settings(self, policy, iface, exception):
        with pytest.raises(exception):
            policy.remember(sentinel.request, sentinel.userid, iface=iface)

    @pytest.fixture
    def policy(self, sub_policies):
        return CascadingAuthenticationPolicy(sub_policies)

    @pytest.fixture
    def sub_policies(self):
        sub_policies = [
            create_autospec(SessionAuthenticationPolicy, instance=True, spec_set=True),
            create_autospec(
                BasicAuthAuthenticationPolicy, instance=True, spec_set=True
            ),
        ]

        for pos, policy in enumerate(sub_policies):
            policy.authenticated_userid.return_value = f"user_{pos}"

        return sub_policies


class TestAuthorizationPolicy:
    @pytest.mark.parametrize(
        "permission,principals,expected_result",
        [
            # API-authenticated requests get the CHECK_URL permission.
            (
                Permissions.CHECK_URL,
                [Everyone, Authenticated, "dev", Principals.API],
                Allowed,
            ),
            # Other requests don't get the check_url permission.
            (Permissions.CHECK_URL, [Everyone, Authenticated], Denied),
        ],
    )
    def test_it(self, policy, permission, principals, expected_result):
        result = policy.permits(sentinel.contest, principals, permission)

        assert isinstance(result, expected_result)

    @pytest.fixture
    def policy(self):
        return AuthorizationPolicy()
