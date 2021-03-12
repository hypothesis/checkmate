"""User feedback for blocked pages."""

from pyramid.view import view_config

from checkmate.exceptions import ResourceConflict
from checkmate.models import AllowRule, Detection, Principals, Reason, Source
from checkmate.services import URLCheckerService
from checkmate.url import hash_for_rule
from checkmate.validation import get_validated_json_body, get_validator

_ALLOW_LIST_DETECTION = Detection(Reason.NOT_ALLOWED, Source.ALLOW_LIST)
_ALLOW_RULE_VALIDATOR = get_validator("resource/schema/AllowRule.json")


@view_config(
    route_name="add_to_allow_list",
    request_method="POST",
    renderer="json",
    effective_principals=[Principals.STAFF],
)
def add_to_allow_list(_context, request):
    """Render an HTML version of a blocked URL with explanation."""

    body = get_validated_json_body(request, _ALLOW_RULE_VALIDATOR)
    url = body["data"]["meta"]["url"]

    # Check this isn't something really dumb like 'co.uk' which will ruin the
    # allow list

    # Don't fail fast, so we get all of the detections
    checker = request.find_service(URLCheckerService)
    reasons = list(checker.check_url(url, fail_fast=False))

    try:
        # We expect a detection from not being on the allow list, so we'll
        # remove it, which will trigger a ValueError if it wasn't there
        reasons.remove(_ALLOW_LIST_DETECTION)
    except ValueError:
        raise ResourceConflict("Requested URL is already allowed") from None

    # After the expected allow list detection is gone, any remaining
    # reasons are because the URL is blocked
    if reasons:
        raise ResourceConflict(f"Cannot allow URL as reasons to block found: {reasons}")

    rule_string, hex_hash = hash_for_rule(url)

    rule = AllowRule(rule=rule_string, hash=hex_hash, tags=["manual"])
    request.db.add(rule)
    request.db.flush()  # Make sure an id is allocated before we serialise

    # https://jsonapi.org/format/#document-top-level
    return {"data": rule.to_json_api()}
