"""The main application entrypoint module."""
import logging
import os

import pyramid.config
import pyramid_tm

logger = logging.getLogger(__name__)


class CheckmateConfigurator:
    def __init__(self, config, celery_worker=False):
        self.config = config
        self.celery_worker = celery_worker

        self._configure_logging(config)
        self._configure_db(config)
        self._configure_sentry(config)
        self._configure_checkmate(config)
        self._configure_api_auth(config)

    def add_setting_from_env(self, param_name):
        value = self.config.registry.settings.get(param_name) or os.environ.get(
            param_name.upper()
        )
        if value is None:
            raise ValueError(f"Param {param_name} must be provided.")

        self.config.add_settings({param_name: value})

    def _configure_checkmate(self, config):
        if self.celery_worker:
            self.add_setting_from_env("checkmate_blocklist_url")
        else:
            # The celery workers don't need to know about this stuff

            # Include the secret for crytographic functions
            self.add_setting_from_env("checkmate_secret")

            config.include("pyramid_services")
            config.include("checkmate.services")

            config.include("pyramid_jinja2")
            config.scan("checkmate.views")
            config.include("checkmate.routes")

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
        # Configure sentry
        config.add_settings(
            {
                "h_pyramid_sentry.filters": [],
                "h_pyramid_sentry.sqlalchemy_support": True,
            }
        )
        if self.celery_worker:
            config.add_settings({"h_pyramid_sentry.celery_support": True})

        config.include("h_pyramid_sentry")

    @classmethod
    def _configure_api_auth(cls, config):
        api_keys = {}
        for envvar_name, envvar_value in os.environ.items():
            if not envvar_name.startswith("CHECKMATE_API_KEY_"):
                continue

            username = envvar_name.split("CHECKMATE_API_KEY_")[1].lower()

            api_keys[envvar_value] = username
            logger.info("Loaded api_key value for %s", username)

        config.add_settings({"api_keys": api_keys})


def create_app(_=None, celery_worker=False, **settings):  # pragma: no cover
    """Configure and return the WSGI app."""

    config = pyramid.config.Configurator(settings=settings)
    CheckmateConfigurator(config=config, celery_worker=celery_worker)

    return config.make_wsgi_app()
