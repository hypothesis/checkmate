"""The routes for the Pyramid app."""


def add_routes(config):
    """Register all routes."""

    config.add_route("root", "/")

    config.add_route("status", "/_status")
    config.add_route("check_url", "/api/check")

    # Serve content from the static/static directory at /static
    config.add_static_view("static", "static/static", cache_max_age=3600)

    config.add_route("present_block", "/block")

    config.add_route("admin.index", "/admin/")
    config.add_route("admin.allow_url", "/admin/allow_url/")
    config.add_route("admin.block_list", "/admin/block_list/")

    config.add_route("add_to_allow_list", "/api/rule", request_method="POST")


def includeme(config):  # pragma: no cover
    """Pyramid config."""
    add_routes(config)
