from checkmatelib.url import CanonicalURL, Domain
from marshmallow import ValidationError
from marshmallow_jsonapi import Schema, fields
from pyramid.view import view_config

from checkmate.security import Permissions
from checkmate.services import RuleService


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


@view_config(
    route_name="add_to_allow_list",
    request_method="POST",
    jsonapi={"schema": AllowRuleSchema()},
    permission=Permissions.ADD_TO_ALLOW_LIST,
)
def add_to_allow_list(request):
    """Add a rule matching `url` to the allow list."""

    return request.find_service(RuleService).add_to_allow_list(
        request.jsonapi.attributes["url"]
    )
