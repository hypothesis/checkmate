"""The views for the Pyramid app."""


def includeme(config):  # pragma: no cover
    """Pyramid config."""
    config.scan("checkmate.views")
