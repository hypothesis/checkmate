from checkmate.services.custom_rule import CustomRuleService
from checkmate.services.rule import RuleService
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
        "checkmate.services.rule.factory", iface=RuleService
    )
    config.register_service_factory(
        "checkmate.services.custom_rule.factory", iface=CustomRuleService
    )
