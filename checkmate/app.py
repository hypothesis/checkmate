"""The main application entrypoint module."""
import os

import pyramid.config
import pyramid_tm


OPTIONAL_PARAMS = ["database_url"]

def load_settings(settings, celery_worker=False):
    """Load application settings from a dict or environment variables.

    Checks that the required parameters are either filled out in the provided
    dict, or that the required values can be loaded from the environment.

    :param settings: Settings dict
    :raise ValueError: If a required parameter is not filled
    :return: A dict of settings
    """

    for param in OPTIONAL_PARAMS:  # pragma: no cover
        value = settings.get(param, os.environ.get(param.upper()))
        if value:
            settings[param] = value

    required_params = ["checkmate_blocklist_path"]
    if celery_worker:
        required_params.append("checkmate_blocklist_url")

    for param in required_params:
        value = settings[param] = settings.get(param, os.environ.get(param.upper()))

        if value is None:
            raise ValueError(f"Param {param} must be provided.")

    # Configure sentry
    settings["h_pyramid_sentry.filters"] = []
    if celery_worker:
        settings["h_pyramid_sentry.celery_support"] = True

    return settings


def create_app(_=None, celery_worker=False, **settings):  # pragma: no cover
    """Configure and return the WSGI app."""

    settings = load_settings(settings, celery_worker)
    config = pyramid.config.Configurator(settings=settings)

    # Make sure that pyramid_exclog's tween runs under pyramid_tm's tween so
    # that pyramid_exclog doesn't re-open the DB session after pyramid_tm has
    # already closed it.
    config.add_tween(
        "pyramid_exclog.exclog_tween_factory", under="pyramid_tm.tm_tween_factory"
    )
    config.add_settings({"exclog.extra_info": True})
    config.include("pyramid_exclog")

    # Use pyramid_tm's explicit transaction manager.
    #
    # This means that trying to access a request's transaction after pyramid_tm
    # has closed the request's transaction will crash, rather than implicitly
    # opening a new transaction that doesn't get closed (and potentially
    # leaking open DB connections).
    #
    # This is recommended in the pyramid_tm docs:
    #
    # https://docs.pylonsproject.org/projects/pyramid_tm/en/latest/#custom-transaction-managers
    config.registry.settings["tm.manager_hook"] = pyramid_tm.explicit_manager

    config.include("pyramid_tm")

    config.include("h_pyramid_sentry")

    if not celery_worker:
        # The celery workers don't need to know about this stuff
        config.include("pyramid_jinja2")

        config.include("checkmate.views")
        config.include("checkmate.routes")

    # Give the models a once over, so that they are registered to SQLAlchemy
    config.scan("checkmate.models.data")
    config.include("checkmate.db")

    return config.make_wsgi_app()
