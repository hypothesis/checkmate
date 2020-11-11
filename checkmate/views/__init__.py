"""The views for the Pyramid app."""


def add_routes(config):
    """Add routes to pyramid config."""
    config.add_route("get_status", "/_status")


def includeme(config):
    """Pyramid config."""
    add_routes(config)
    config.scan(__name__)
