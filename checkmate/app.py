"""The main application entrypoint module."""
import os

import pyramid.config

REQUIRED_PARAMS = ["checkmate_blocklist_path"]


def load_settings(settings):
    """Load application settings from a dict or environment variables.

    Checks that the required parameters are either filled out in the provided
    dict, or that the required values can be loaded from the environment.

    :param settings: Settings dict
    :raise ValueError: If a required parameter is not filled
    :return: A dict of settings
    """
    for param in REQUIRED_PARAMS:
        value = settings[param] = settings.get(param, os.environ.get(param.upper()))

        if value is None:
            raise ValueError(f"Param {param} must be provided.")

    # Configure sentry
    settings["h_pyramid_sentry.filters"] = []

    return settings


def create_app(_=None, **settings):  # pragma: no cover
    """Configure and return the WSGI app."""

    config = pyramid.config.Configurator(settings=load_settings(settings))

    config.include("pyramid_jinja2")
    config.include("h_pyramid_sentry")

    config.include("checkmate.views")
    config.include("checkmate.routes")

    return config.make_wsgi_app()
