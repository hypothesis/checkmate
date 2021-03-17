from enum import Enum
from typing import List, NamedTuple

from pyramid.authentication import (
    SessionAuthenticationHelper,
    extract_http_basic_credentials,
)
from pyramid.security import Allowed, Denied


class Permissions(Enum):
    ADMIN = "admin"
    CHECK_URL = "check_url"
    ADD_TO_ALLOW_LIST = "add_to_allow_list"


class Identity(NamedTuple):
    userid: str
    permissions: List[str]


class CascadingSecurityPolicy:
    def __init__(self, subpolicies):
        self._subpolicies = subpolicies

    def identity(self, request):
        return self._effective_subpolicy(request).identity(request)

    def authenticated_userid(self, request):
        return self._effective_subpolicy(request).authenticated_userid(request)

    def permits(self, request, context, permission):
        return self._effective_subpolicy(request).permits(request, context, permission)

    def forget(self, request, **kwargs):
        return self._effective_subpolicy(request).forget(request, **kwargs)

    def remember(self, request, userid, iface, **kwargs):
        return self._get_specific_policy(iface).remember(request, userid, **kwargs)

    def _effective_subpolicy(self, request):
        for policy in self._subpolicies:
            if policy.authenticated_userid(request):
                return policy

        return self._subpolicies[-1]

    def _get_specific_policy(self, iface):
        for policy in self._subpolicies:
            if isinstance(policy, iface):
                return policy

        raise KeyError(
            f"Could not find a policy matching the requested interface: {iface}"
        )


class SecurityPolicy(CascadingSecurityPolicy):
    def __init__(self):
        super().__init__(
            subpolicies=[HTTPBasicAuthSecurityPolicy(), GoogleSecurityPolicy()]
        )


class GoogleSecurityPolicy:
    def __init__(self):
        self._session_authentication_helper = SessionAuthenticationHelper()

    def identity(self, request):
        userid = self.authenticated_userid(request)

        if userid and userid.endswith("@hypothes.is"):
            return Identity(
                userid, permissions=[Permissions.ADMIN, Permissions.ADD_TO_ALLOW_LIST]
            )

        return Identity("", [])

    def authenticated_userid(self, request):
        return self._session_authentication_helper.authenticated_userid(request)

    def permits(self, request, context, permission):
        return _permits(self, request, context, permission)

    def remember(self, request, userid, **kwargs):
        return self._session_authentication_helper.remember(request, userid, **kwargs)

    def forget(self, request, **kwargs):
        return self._session_authentication_helper.forget(request, **kwargs)


class HTTPBasicAuthSecurityPolicy:
    def identity(self, request):
        userid = self.authenticated_userid(request)

        if userid:
            return Identity(userid, permissions=[Permissions.CHECK_URL])

        return Identity("", [])

    def authenticated_userid(self, request):  # pylint:disable=no-self-use
        credentials = extract_http_basic_credentials(request)

        if credentials:
            return request.registry.settings["api_keys"].get(credentials.username)

        return None

    def permits(self, request, context, permission):
        return _permits(self, request, context, permission)

    def remember(self, request, userid, **kwargs):
        pass

    def forget(self, request, **kwargs):
        pass


def _permits(policy, request, _context, permission):
    if permission in policy.identity(request).permissions:
        return Allowed("allowed")

    return Denied("denied")
