from checkmate.services.secure_link import SecureLinkService


def includeme(config):  # pragma: no cover
    config.register_service_factory(
        "checkmate.services.secure_link.factory",
        iface=SecureLinkService,
    )
