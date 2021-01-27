from functools import lru_cache


class CascadingAuthenticationPolicy:
    """Top-level authentication policy that delegates to sub-policies."""

    def __init__(self, policies):
        self._policies = policies

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
        for policy in self._policies:
            if policy.authenticated_userid(request):
                return policy

        return self._policies[-1]
