import logging

from pyramid.authentication import (
    BasicAuthAuthenticationPolicy,
    extract_http_basic_credentials,
)

logger = logging.getLogger(__name__)

APIAuthenticated = "APIAuthenticated"  # pylint: disable=invalid-name


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
            return [APIAuthenticated]

        return None
