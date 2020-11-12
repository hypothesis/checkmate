"""The routes for the Pyramid app."""


def includeme(config):  # pragma: no cover
    """Pyramid config."""
    config.add_route("get_status", "/_status")
    config.add_route("url_check", "/api/url")
