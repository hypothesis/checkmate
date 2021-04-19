"""The routes for the Pyramid app."""


def add_routes(config):
    """Register all routes."""

    config.add_route("root", "/")

    config.add_route("get_status", "/_status")
    config.add_route("check_url", "/api/check")

    # Serve content from the static/static directory at /ui/static
    config.add_static_view("ui/static", "static/static", cache_max_age=3600)

    config.add_route("present_block", "/ui/block")
    config.add_route("admin_pages", "/ui/admin")

    config.add_route("add_to_allow_list", "/ui/api/rule", request_method="POST")


def includeme(config):  # pragma: no cover
    """Pyramid config."""
    add_routes(config)
