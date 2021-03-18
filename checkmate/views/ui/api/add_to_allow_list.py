from marshmallow import ValidationError
from marshmallow_jsonapi import Schema, fields
from pyramid.view import view_config
from webargs.pyramidparser import use_kwargs

from checkmate.models import Principals
from checkmate.services import RuleService
from checkmate.url import CanonicalURL, Domain


def _check_public_url(instance):
    """Check that a given URL is publicly available.

    This only uses static data, not an actual check online.
    """
    _, netloc, _, _, _, _ = CanonicalURL.canonical_split(instance)
    domain = Domain(netloc)
    if not domain.is_valid:
        raise ValidationError("The URL does not have a valid domain")

    if not domain.is_public:
        raise ValidationError("The URL is not public")

    return True


class AllowRuleSchema(Schema):
    id = fields.Int(dump_only=True)
    hash = fields.Str(dump_only=True)
    rule = fields.Str(dump_only=True)
    force = fields.Bool(dump_only=True)
    tags = fields.List(fields.Str(), dump_only=True)

    url = fields.Str(load_only=True, validate=_check_public_url, required=True)

    class Meta:
        type_ = "AllowRule"
        strict = True


_ALLOW_RULE_SCHEMA = AllowRuleSchema()


@view_config(
    route_name="add_to_allow_list",
    request_method="POST",
    renderer="json",
    effective_principals=[Principals.STAFF],
)
@use_kwargs(_ALLOW_RULE_SCHEMA)
def add_to_allow_list(request, url):
    """Add a rule matching `url` to the allow list."""
    rule = request.find_service(RuleService).add_to_allow_list(url)

    return _ALLOW_RULE_SCHEMA.dump(rule)
