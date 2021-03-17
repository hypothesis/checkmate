from base64 import b64encode
from unittest.mock import call, create_autospec, sentinel

import pytest
from pyramid.security import Allowed, Denied

from checkmate.security import (
    CascadingSecurityPolicy,
    GoogleSecurityPolicy,
    HTTPBasicAuthSecurityPolicy,
    Identity,
    Permissions,
)


class SecurityPolicy:  # pragma: no cover
    """Spec for the subpolicy1 and subpolicy2 fixtures."""

    def identity(self, request):
        pass

    def authenticated_userid(self, request):
        pass

    def permits(self, request, context, permission):
        pass

    def remember(self, request, userid, **kw):
        pass

    def forget(self, request, **kw):
        pass


class SubPolicy1(SecurityPolicy):
    """The class that the subpolicy1 fixture is an instance of."""


class SubPolicy2(SecurityPolicy):
    """The class that the subpolicy2 fixture is an instance of."""


class TestCascadingSecurityPolicy:
    def test_identity(self, policy, effective_subpolicy):
        assert (
            policy.identity(sentinel.request)
            == effective_subpolicy.identity.return_value
        )
        effective_subpolicy.identity.assert_called_once_with(sentinel.request)

    def test_authenticated_userid(self, policy, effective_subpolicy):
        assert (
            policy.authenticated_userid(sentinel.request)
            == effective_subpolicy.authenticated_userid.return_value
        )
        assert effective_subpolicy.authenticated_userid.call_args == call(
            sentinel.request
        )

    def test_permits(self, policy, effective_subpolicy):
        assert (
            policy.permits(sentinel.request, sentinel.context, sentinel.permission)
            == effective_subpolicy.permits.return_value
        )
        effective_subpolicy.permits.assert_called_once_with(
            sentinel.request, sentinel.context, sentinel.permission
        )

    def test_forget(self, policy, effective_subpolicy):
        assert (
            policy.forget(sentinel.request) == effective_subpolicy.forget.return_value
        )
        effective_subpolicy.forget.assert_called_once_with(sentinel.request)

    def test_forget_passes_kwargs_to_subpolicy(self, policy, effective_subpolicy):
        policy.forget(sentinel.request, foo="foo", bar="bar")

        assert effective_subpolicy.forget.call_args[1] == {"foo": "foo", "bar": "bar"}

    @pytest.mark.parametrize(
        "iface,subpolicy", [(SubPolicy1, "subpolicy1"), (SubPolicy2, "subpolicy2")]
    )
    def test_remember(
        self,
        iface,
        subpolicy,
        policy,
        subpolicy1,  # pylint:disable=unused-argument
        subpolicy2,  # pylint:disable=unused-argument
    ):
        # The subpolicy whose remember() method we expect to get called,
        # either subpolicy1 or subpolicy2.
        subpolicy = locals()[subpolicy]

        assert (
            policy.remember(sentinel.request, sentinel.userid, iface)
            == subpolicy.remember.return_value
        )

    def test_remember_passes_kwargs_to_subpolicy(self, policy, subpolicy1):
        policy.remember(
            sentinel.request, sentinel.userid, SubPolicy1, foo="foo", bar="bar"
        )

        assert subpolicy1.remember.call_args[1] == {"foo": "foo", "bar": "bar"}

    def test_remember_raises_KeyError_if_iface_not_found(self, policy):
        class UnknownPolicy:
            """An unknown security policy class."""

        with pytest.raises(KeyError):
            policy.remember(sentinel.request, sentinel.userid, UnknownPolicy)

    @pytest.fixture
    def policy(self, subpolicy1, subpolicy2):
        """Return the CascadingSecurityPolicy instance to be tested."""
        return CascadingSecurityPolicy([subpolicy1, subpolicy2])

    @pytest.fixture(params=["subpolicy1", "subpolicy2", "both", None])
    def effective_subpolicy(
        self,
        request,
        subpolicy1,
        subpolicy2,
    ):
        """Return the subpolicy that the test expects to be effective."""

        # Any test that uses this parametrized `effective_subpolicy` fixture
        # will get run four times...

        if request.param == "subpolicy1":
            # The first time the test is run subpolicy1.authenticated_userid()
            # will return a userid but subpolicy2.authenticated_userid() won't.
            subpolicy1.authenticated_userid.return_value = sentinel.policy1_userid
            subpolicy2.authenticated_userid.return_value = None
            # CascadingSecurityPolicy should choose subpolicy1 as the effective policy.
            return subpolicy1

        if request.param == "subpolicy2":
            # The next time the test is run subpolicy1.authenticated_userid()
            # *won't* return a userid but subpolicy2.authenticated_userid() will.
            subpolicy1.authenticated_userid.return_value = None
            subpolicy2.authenticated_userid.return_value = sentinel.policy2_userid
            # CascadingSecurityPolicy should choose subpolicy2 as the effective policy.
            return subpolicy2

        if request.param == "both":
            # The next time the test is run both subpolicies will return a userid.
            subpolicy1.authenticated_userid.return_value = sentinel.policy1_userid
            subpolicy2.authenticated_userid.return_value = sentinel.policy2_userid
            # CascadingSecurityPolicy should choose subpolicy1 as the effective policy.
            return subpolicy1

        # The final time the test is run neither subpolicy will return a userid.
        assert request.param is None
        subpolicy1.authenticated_userid.return_value = None
        subpolicy2.authenticated_userid.return_value = None
        # CascadingSecurityPolicy should choose subpolicy2 as the effective policy.
        return subpolicy2

    @pytest.fixture
    def subpolicy1(self):
        """Return the first subpolicy passed to CascadingSecurityPolicy(subpolicies)."""
        return create_autospec(SubPolicy1, spec_set=True, instance=True)

    @pytest.fixture
    def subpolicy2(self):
        """Return the second subpolicy passed to CascadingSecurityPolicy(subpolicies)."""
        return create_autospec(SubPolicy2, spec_set=True, instance=True)


class TestGoogleSecurityPolicy:
    @pytest.mark.parametrize(
        "userid,expected_identity",
        [
            (
                "testuser@hypothes.is",
                Identity(
                    "testuser@hypothes.is",
                    [Permissions.ADMIN, Permissions.ADD_TO_ALLOW_LIST],
                ),
            ),
            (
                "testuser@example.com",
                Identity(
                    "",
                    [],
                ),
            ),
        ],
    )
    def test_identity(self, policy, pyramid_request, userid, expected_identity):
        pyramid_request.session["auth.userid"] = userid

        assert policy.identity(pyramid_request) == expected_identity

    def test_identity_when_no_user_is_logged_in(self, policy, pyramid_request):
        assert policy.identity(pyramid_request) == Identity("", [])

    def test_authenticated_userid(self, policy, pyramid_request):
        pyramid_request.session["auth.userid"] = "testuser@hypothes.is"

        assert policy.authenticated_userid(pyramid_request) == "testuser@hypothes.is"

    @pytest.mark.parametrize(
        "permission,expected_result",
        [
            (Permissions.ADMIN, Allowed("allowed")),
            (Permissions.CHECK_URL, Denied("denied")),
        ],
    )
    def test_permits(self, policy, pyramid_request, permission, expected_result):
        pyramid_request.session["auth.userid"] = "testuser@hypothes.is"

        assert (
            policy.permits(pyramid_request, sentinel.context, permission)
            == expected_result
        )

    def test_remember(self, policy, pyramid_request):
        assert policy.remember(pyramid_request, "testuser@hypothes.is") == []

    def test_forget(self, policy, pyramid_request):
        assert policy.forget(pyramid_request) == []

    @pytest.fixture
    def policy(self):
        return GoogleSecurityPolicy()


class TestHTTPBasicAuthSecurityPolicy:
    def test_identity_when_there_is_a_userid(self, policy, pyramid_request):
        self.set_authorization_header(pyramid_request, "password")

        identity = policy.identity(pyramid_request)

        assert identity == Identity("userid", [Permissions.CHECK_URL])

    def test_identity_when_theres_no_userid(self, policy, pyramid_request):
        identity = policy.identity(pyramid_request)

        assert identity == Identity("", [])

    @pytest.mark.parametrize(
        "password,expected_userid", [("password", "userid"), ("unknown_password", None)]
    )
    def test_authenticated_userid(
        self, policy, pyramid_request, password, expected_userid
    ):
        self.set_authorization_header(pyramid_request, password)

        assert policy.authenticated_userid(pyramid_request) == expected_userid

    def test_authenticated_userid_when_there_are_no_credentials(
        self, policy, pyramid_request
    ):
        assert policy.authenticated_userid(pyramid_request) is None

    @pytest.mark.parametrize(
        "permission,expected_result",
        [
            (Permissions.CHECK_URL, Allowed("allowed")),
            (Permissions.ADD_TO_ALLOW_LIST, Denied("denied")),
        ],
    )
    def test_permits(self, policy, pyramid_request, permission, expected_result):
        self.set_authorization_header(pyramid_request, "password")

        assert (
            policy.permits(pyramid_request, sentinel.context, permission)
            == expected_result
        )

    def test_remember(self, policy, pyramid_request):
        assert policy.remember(pyramid_request, sentinel.userid) is None

    def test_forget(self, policy, pyramid_request):
        assert policy.forget(pyramid_request) is None

    def set_authorization_header(self, pyramid_request, password):
        # HTTPBasicAuthSecurityPolicy works by requiring the request to contain
        # a password in the HTTP Basic Auth *username* field.
        #
        # That password is then used to look up a username in the settings (see
        # the pyramid_request fixture below.)
        #
        # Set the necessary HTTP Basic Auth header for the request to be
        # authenticated with `password` in the HTTP Basic Auth username field.
        pyramid_request.headers["Authorization"] = (
            "Basic " + b64encode(f"{password}:".encode()).decode()
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        # If the request contains "password" in the HTTP Basic Auth username
        # field then the user will be authenticated as "userid".
        pyramid_request.registry.settings["api_keys"] = {"password": "userid"}

        return pyramid_request

    @pytest.fixture
    def policy(self):
        return HTTPBasicAuthSecurityPolicy()
