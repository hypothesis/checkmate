from functools import lru_cache


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
