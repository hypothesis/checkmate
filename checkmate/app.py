"""The main application entrypoint module."""

import logging
import os
import re

import pyramid.config
import pyramid_tm
from pyramid.session import SignedCookieSessionFactory
from sentry_sdk.types import Hint, Log

from checkmate._version import get_version
from checkmate.security import SecurityPolicy

logger = logging.getLogger(__name__)

API_KEY_RE = re.compile(r"^CHECKMATE_API_KEY_(?P<user>.*)$")


def sentry_before_send_log(log: Log, _hint: Hint) -> Log | None:
    """Filter out log messages that we don't want to send to Sentry Logs."""

    if log.get("attributes", {}).get("logger.name") == "gunicorn.access":
        return None

    return log


class CheckmateConfigurator:
    def __init__(self, config, celery_worker=False):
        self.config = config
        self.celery_worker = celery_worker

        self._configure_logging(config)
        self._configure_db(config)
        self._configure_sentry(config)
        if not celery_worker:
            self._configure_auth(config)

        self._configure_checkmate(config)

    @property
    def is_dev(self):
        """Get whether we are running in Dev."""

        return bool(self.config.registry.settings.get("dev"))

    def add_setting_from_env(self, param_name, default=None, env_var_name=None):
        env_var_name = env_var_name.upper() if env_var_name else param_name.upper()

        value = self.config.registry.settings.get(param_name) or os.environ.get(
            env_var_name
        )
        if value is None and default is None:
            raise ValueError(f"Param {param_name} must be provided.")

        self.config.add_settings({param_name: value or default})

        return value

    def add_api_keys_from_env(self, param_name):
        keys = self.config.registry.settings.get(param_name, {})

        for name, api_key in os.environ.items():
            match = API_KEY_RE.match(name)
            if match:
                username = match.group("user").lower()
                logger.info("Loaded api_key value for %s", username)
                keys[api_key] = username

        self.config.add_settings({param_name: keys})

        return keys

    def _configure_checkmate(self, config):
        if not self.celery_worker:
            # The celery workers don't need to know about this stuff

            config.include("pyramid_services")
            config.include("checkmate.services")

            config.include("pyramid_jinja2")
            config.scan("checkmate.views")
            config.include("checkmate.routes")
            config.include("checkmate.views.derivers")

            self.add_setting_from_env("public_scheme", default="https")
            self.add_setting_from_env("public_port", default="443")
            self.add_setting_from_env("public_host")

        # pyramid-sanity should be activated as late as possible
        config.include("pyramid_sanity")

    @classmethod
    def _configure_logging(cls, config):
        # Make sure that pyramid_exclog's tween runs under pyramid_tm's tween
        # so that pyramid_exclog doesn't re-open the DB session after
        # pyramid_tm has already closed it.
        config.add_tween(
            "pyramid_exclog.exclog_tween_factory", under="pyramid_tm.tm_tween_factory"
        )

        config.add_settings({"exclog.extra_info": True})
        config.include("pyramid_exclog")

    def _configure_db(self, config):
        self.add_setting_from_env("database_url")
        config.include("checkmate.models")
        config.include("checkmate.db")

        # Use pyramid_tm's explicit transaction manager.
        config.include("pyramid_tm")

        # This means that trying to access a request's transaction after
        # pyramid_tm has closed the request's transaction will crash, rather
        # than implicitly opening a new transaction that doesn't get closed
        # (and potentially leaking open DB connections).

        # This is recommended in the pyramid_tm docs:
        # https://docs.pylonsproject.org/projects/pyramid_tm/en/latest/#custom-transaction-managers
        config.add_settings({"tm.manager_hook": pyramid_tm.explicit_manager})

    def _configure_sentry(self, config):
        config.add_settings(
            {
                "h_pyramid_sentry.filters": [],
                "h_pyramid_sentry.sqlalchemy_support": True,
                # Enable Sentry's "Releases" feature, see:
                # https://docs.sentry.io/platforms/python/configuration/options/#release
                #
                # h_pyramid_sentry passes any h_pyramid_sentry.init.* Pyramid settings
                # through to sentry_sdk.init(), see:
                # https://github.com/hypothesis/h-pyramid-sentry?tab=readme-ov-file#settings
                #
                # For the full list of options that sentry_sdk.init() supports see:
                # https://docs.sentry.io/platforms/python/configuration/options/
                "h_pyramid_sentry.init.release": get_version(),
                "h_pyramid_sentry.init.enable_logs": True,
                "h_pyramid_sentry.init.before_send_log": sentry_before_send_log,
            }
        )
        if self.celery_worker:
            config.add_settings({"h_pyramid_sentry.celery_support": True})

        config.include("h_pyramid_sentry")

    def _configure_auth(self, config):
        # Same value for both signature service and pyramid_googleauth
        checkmate_secret = self.add_setting_from_env("checkmate_secret")
        checkmate_secret = self.add_setting_from_env(
            "pyramid_googleauth.secret", env_var_name="checkmate_secret"
        )

        # Add values expected by the Google Auth service
        self.add_setting_from_env(
            "pyramid_googleauth.google_client_id", env_var_name="google_client_id"
        )
        self.add_setting_from_env(
            "pyramid_googleauth.google_client_secret",
            env_var_name="google_client_secret",
        )

        # API keys used by APIHTTPAuth
        self.add_api_keys_from_env("api_keys")

        config.include("pyramid_googleauth")
        config.add_settings({"pyramid_googleauth.login_success_redirect_url": "/admin"})

        # Setup a cookie based session to store our authentication details in
        session_factory = SignedCookieSessionFactory(
            checkmate_secret,
            # Lock down the cookie as much as we can
            httponly=True,
            secure=not self.is_dev,
            # Forward compatibility with Pyramid 2.0 defaults
            serializer=pyramid.session.JSONSerializer(),
        )
        config.set_session_factory(session_factory)

        config.set_security_policy(SecurityPolicy())


def create_app(_=None, celery_worker=False, **settings):  # pragma: no cover
    """Configure and return the WSGI app."""

    config = pyramid.config.Configurator(settings=settings)
    CheckmateConfigurator(config=config, celery_worker=celery_worker)

    return config.make_wsgi_app()
