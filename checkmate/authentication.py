from functools import lru_cache

from pyramid.authentication import (
    BasicAuthAuthenticationPolicy,
    extract_http_basic_credentials,
)

from checkmate.models import Principals


class CascadingAuthenticationPolicy:
    """Top-level authentication policy that delegates to sub-policies."""

    def __init__(self, sub_policies):
        """Create a policy which delegates to the first policy with a user.

        :param sub_policies: List of at least one policy
        :raise ValueError: If no policies are passed
        """
        if not sub_policies:
            raise ValueError("You must supply at least one policy")

        self._sub_policies = sub_policies

    def authenticated_userid(self, request):
        return self.effective_policy(request).authenticated_userid(request)

    def unauthenticated_userid(self, request):
        return self.effective_policy(request).unauthenticated_userid(request)

    def effective_principals(self, request):
        return self.effective_policy(request).effective_principals(request)

    def remember(self, request, userid, **kw):
        return self.effective_policy(request).remember(request, userid, **kw)

    def forget(self, request):
        return self.effective_policy(request).forget(request)

    @lru_cache(1)
    def effective_policy(self, request):
        """Get the first policy with a user.

        If no policies return a user, the last policy is returned.
        :param request: Pyramid request to get the user from
        :return: One of the sub policies in this object
        """
        for policy in self._sub_policies:
            if policy.authenticated_userid(request):
                return policy

        return self._sub_policies[-1]


class APIHTTPAuth(BasicAuthAuthenticationPolicy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def unauthenticated_userid(self, request):
        """Overridden to return the api username.

        The user linked to that api_key is stored on settings[api_keys].
        """
        credentials = extract_http_basic_credentials(request)

        if credentials:
            return request.registry.settings["api_keys"].get(credentials.username)

        return None

    @staticmethod
    def check_callback(http_username, _, request):
        """Implement callback for APIHTTPAuth(BasicAuthAuthenticationPolicy).

        Expected to return None if the userid doesn't exist or a sequence of
        principal identifiers (possibly empty) if the user does exist.

        """
        # BasicAuth uses a pair of user/pass but we are just using
        # the api_key in the username place leaving password empty.
        # api_keys is api_key => username dict
        api_keys = request.registry.settings["api_keys"]
        api_username = api_keys.get(http_username)
        if api_username:
            return [Principals.API]

        return None
