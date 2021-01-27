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
    config.add_route("admin_login_failure", "/ui/admin/login_failure")

    config.add_route("login", "/ui/api/login")
    config.add_route("login_callback", "/ui/api/login_callback")
    config.add_route("logout", "/ui/api/logout")


def includeme(config):  # pragma: no cover
    """Pyramid config."""
    add_routes(config)
