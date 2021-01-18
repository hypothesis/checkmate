from checkmate.services.secure_link import SecureLinkService
from checkmate.services.url_checker import URLCheckerService


def includeme(config):  # pragma: no cover
    config.register_service_factory(
        "checkmate.services.secure_link.factory", iface=SecureLinkService
    )
    config.register_service_factory(
        "checkmate.services.url_checker.factory", iface=URLCheckerService
    )
