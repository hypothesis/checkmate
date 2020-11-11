"""The views for the Pyramid app."""


def add_routes(config):  # pragma: no cover
    """Add routes to pyramid config."""
    config.add_route("get_status", "/_status")
    config.add_route("url_check", "/api/url")


def includeme(config):  # pragma: no cover
    """Pyramid config."""
    add_routes(config)
    config.scan(__name__)
