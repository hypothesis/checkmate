from unittest.mock import call, create_autospec

import pytest
from pyramid.authentication import SessionAuthenticationPolicy

from checkmate.authentication import CascadingAuthenticationPolicy

# pylint: disable=protected-access


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
        "method,args,kwargs",
        (
            ("authenticated_userid", ["request"], {}),
            ("unauthenticated_userid", ["request"], {}),
            ("effective_principals", ["request"], {}),
            ("remember", ["request", "userid"], {"k": "v"}),
            ("forget", ["request"], {}),
        ),
    )
    def test_method_pass_through(self, method, args, kwargs, policy):
        result = getattr(policy, method)(*args, **kwargs)

        # We should use effective_policy here, but it messes up the counts
        proxied_method = getattr(policy._sub_policies[0], method)
        assert result == proxied_method.return_value

        if method == "authenticated_userid":
            proxied_method.assert_has_calls(
                [call(*args, **kwargs), call(*args, **kwargs)]
            )
        else:
            proxied_method.assert_called_once_with(*args, **kwargs)

    @pytest.fixture
    def policy(self, sub_policies):
        return CascadingAuthenticationPolicy(sub_policies)

    @pytest.fixture
    def sub_policies(self):
        sub_policies = [self.get_auth_policy(), self.get_auth_policy()]

        for pos, policy in enumerate(sub_policies):
            policy.authenticated_userid.return_value = f"user_{pos}"

        return sub_policies

    def get_auth_policy(self):
        # Any policy will do, as they should have the same interface
        return create_autospec(
            SessionAuthenticationPolicy, instance=True, spec_set=True
        )
