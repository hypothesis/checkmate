from checkmate.services.google_auth import GoogleAuthService
from checkmate.services.secure_link import SecureLinkService
from checkmate.services.signature import SignatureService
from checkmate.services.url_checker import URLCheckerService


def includeme(config):  # pragma: no cover
    config.register_service_factory(
        "checkmate.services.secure_link.factory", iface=SecureLinkService
    )
    config.register_service_factory(
        "checkmate.services.url_checker.factory", iface=URLCheckerService
    )
    config.register_service(
        SignatureService(secret=config.registry.settings["checkmate_secret"]),
        iface=SignatureService,
    )
    config.register_service_factory(
        "checkmate.services.google_auth.factory", iface=GoogleAuthService
    )
