import os
from urllib.parse import parse_qsl, urlparse

import jwt
from google_auth_oauthlib.flow import Flow
from jwt import InvalidTokenError
from oauthlib.oauth2.rfc6749.errors import InvalidClientError, InvalidGrantError

from checkmate.exceptions import BadOAuth2Config, UserNotAuthenticated
from checkmate.services.signature import SignatureService


class GoogleAuthService:
    # https://developers.google.com/identity/protocols/oauth2/web-server

    # From: https://accounts.google.com/.well-known/openid-configuration
    OPEN_ID_DISCOVERY = {
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
    }

    SCOPES = [
        # Get the email address we will use for the user id
        "https://www.googleapis.com/auth/userinfo.email",
        # Get additional "nice to have" things like the name and picture
        "https://www.googleapis.com/auth/userinfo.profile",
        # This is a default, but includes getting any id info at all
        "openid",
    ]

    def __init__(self, signature_service, client_config):
        """Create a new authentication service object.

        :param signature_service: Instance of SignatureService
        :param client_config: Dict of Google OAuth2 configuration data

        Expected keys of `client_config`:

            * `client_id` - Google provided client id for this environment
            * `client_secret` - Secret which matches the `client_id`
            * `redirect_uri` - Redirect URI registered with Google
        """

        self._signature_service = signature_service

        self._client_id = client_config["client_id"]
        self._client_secret = client_config["client_secret"]
        self._redirect_uri = client_config["redirect_uri"]

        if not self._redirect_uri.startswith("https"):
            # Allow HTTP in dev, otherwise we'll get errors when trying to
            # authenticate with some of the OAuth libraries
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    def login_url(self, login_hint=None, force_login=False):
        """Generate URL for request to Google's OAuth 2.0 server.

        :param login_hint: Pre-fill the form with this email address
        :param force_login: Force a user to login again, even if Google has a
            cookie for them.
        :raise BadOAuth2Config: If our OAuth2 config is incorrect
        :return: A URL to redirect the user to for login
        """

        authorization_url, state = self._get_flow().authorization_url(
            # Enable offline access so that you can refresh an access token
            # without re-prompting the user for permission. Recommended for
            # web server apps.
            access_type="offline",
            # Enable incremental authorization. Recommended as a best practice.
            include_granted_scopes="true",
            # If we happen to know who is logging in, we can pre-fill the form
            login_hint=login_hint,
            # Enable a nonce value we can verify to prevent XSS attacks
            state=self._signature_service.get_nonce(),
            # Should we make the user fill out the form again?
            prompt="select_account" if force_login else None,
        )

        # I'm not sure if we need to check the state coming back from Google,
        # as I think it's just an echo of what we sent, but lets do it anyway
        # as it's quick
        self._assert_state_valid(state)

        return authorization_url

    def exchange_auth_code(self, redirect_url):
        """Handle a callback from Google and get user credentials.

        :param redirect_url: The URL that we received the callback on
        :raise UserNotAuthenticated: If the user fails authentication
        :raise BadOAuth2Config: If our OAuth2 config is incorrect
        :return: A tuple of dicts (user_info, credentials)
        """

        self._assert_redirect_url_valid(redirect_url)

        flow = self._get_flow()
        try:
            flow.fetch_token(authorization_response=redirect_url)

        except InvalidGrantError as err:
            raise UserNotAuthenticated(
                "User is not authenticated: token exchange failed"
            ) from err

        except InvalidClientError as err:
            raise BadOAuth2Config("Bad client or secret") from err

        credentials = flow.credentials

        return (
            self._decode_token(credentials.id_token),
            {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "id_token": credentials.id_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
            },
        )

    def _assert_redirect_url_valid(self, redirect_url):
        query = dict(parse_qsl(urlparse(redirect_url)[4]))

        error = query.get("error")
        if error:
            raise UserNotAuthenticated(f"Error returned from authentication: {error}")

        self._assert_state_valid(query.get("state"))

    def _assert_state_valid(self, state):
        if not self._signature_service.check_nonce(state):
            raise UserNotAuthenticated("State check failed")

    @classmethod
    def _decode_token(cls, id_token):
        """Decode a JWT from Google and verify it."""

        # https://developers.google.com/identity/protocols/oauth2/openid-connect#validatinganidtoken
        try:
            # Don't bother checking this came from Google, we know the request
            # came from Google by virtue of the state/nonce.
            return jwt.decode(id_token, options=dict(verify_signature=False))

        except InvalidTokenError as err:
            # This could actually be because we have the wrong key... but we
            # can't tell the difference, and this is more likely
            raise UserNotAuthenticated(
                "Invalid JWT token: cannot determine user details"
            ) from err

    def _get_flow(self):
        """Get a Google OAuth Flow object."""

        # The google examples show passing "project_id" and "redirect_urls",
        # but they appear to have no effect
        client_args = {
            # Dynamic things
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            # Static things
            "auth_uri": self.OPEN_ID_DISCOVERY["authorization_endpoint"],
            "token_uri": self.OPEN_ID_DISCOVERY["token_endpoint"],
        }

        try:
            flow = Flow.from_client_config({"web": client_args}, scopes=self.SCOPES)
        except ValueError as err:
            raise BadOAuth2Config("The authentication config is invalid") from err

        # Indicate where the API server will redirect the user. This must match
        # our pre-registered redirect URIs.
        flow.redirect_uri = self._redirect_uri

        return flow


def factory(_context, request):
    return GoogleAuthService(
        signature_service=request.find_service(SignatureService),
        client_config={
            # The client id and secret are provided by Google and are different
            # from env to env. So we read these from environment variables in
            # `app.py`
            "client_id": request.registry.settings["google_client_id"],
            "client_secret": request.registry.settings["google_client_secret"],
            # Until this route exists we'll use a hard coded value
            "redirect_uri": request.route_url("login_callback"),
        },
    )
