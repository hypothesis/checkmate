"""The routes for the Pyramid app."""


def includeme(config):  # pragma: no cover
    """Pyramid config."""
    config.add_route("get_status", "/_status")
    config.add_route("check_url", "/api/check")

    # Serve content from the static/static directory at /ui/static
    config.add_static_view("ui/static", "static/static", cache_max_age=3600)

    config.add_route("present_block", "/ui/block")
