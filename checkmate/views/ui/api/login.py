"""User feedback for blocked pages."""

from logging import getLogger

from pyramid.httpexceptions import HTTPFound
from pyramid.security import forget, remember
from pyramid.view import view_config

from checkmate.exceptions import UserNotAuthenticated
from checkmate.services import GoogleAuthService

LOG = getLogger(__name__)


@view_config(route_name="login")
def login(_context, request):
    """Redirect to the Google login prompt."""

    authenticated_email = request.authenticated_userid

    location = request.find_service(GoogleAuthService).login_url(
        # The user is not logged in, so force an account request, otherwise
        # Google might remember the user and put them straight through, making
        # it impossible to really "logout"
        force_login=not bool(authenticated_email),
        # Try to prefill the form with the users email
        login_hint=authenticated_email or request.GET.get("hint"),
    )

    return HTTPFound(location=location)


@view_config(route_name="login_callback")
def login_callback(_context, request):
    """Handle a call back from the Google login prompt."""

    request.session.invalidate()

    google_auth = request.find_service(GoogleAuthService)
    try:
        user, _credentials = google_auth.exchange_auth_code(request.url)

    except UserNotAuthenticated as err:
        # Looks like the user isn't supposed to be here, but we need to give
        # them a way to fix this
        LOG.warning("User failed login", exc_info=err)
        return HTTPFound(location=request.route_url("admin_login_failure"))

    # This doesn't power authentication, just stores useful things around
    request.session.update({"user": user})

    return HTTPFound(
        location=request.route_url("admin_pages"),
        # This causes the users email to be stored as the authenticated user
        headers=remember(request, user["email"]),
    )


@view_config(route_name="logout")
def logout(_context, request):
    """Log the user out and redirect to the login page."""

    user_email = request.authenticated_userid
    request.session.invalidate()

    # Let the login page know the users email before they logged out
    # to make it easier to login
    query = {"hint": user_email} if user_email else None

    # Tell the authentication system to forget the user and redirect
    return HTTPFound(
        location=request.route_url("login", _query=query), headers=forget(request)
    )
