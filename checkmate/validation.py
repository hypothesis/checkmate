"""Validation tools for working with jsonschema."""

import json

from jsonschema import Draft7Validator, FormatChecker, ValidationError
from pkg_resources import resource_stream

from checkmate.exceptions import MalformedJSONBody
from checkmate.url import CanonicalURL, Domain

_FORMAT_CHECKER = FormatChecker()


@_FORMAT_CHECKER.checks("public-url", raises=(ValueError,))
def _check_public_url(instance):
    """A validator which checks that a given URL is publically available.

    This only uses static data, not an actual check online.
    """
    _, netloc, _, _, _, _ = CanonicalURL.canonical_split(instance)
    domain = Domain(netloc)
    if not domain.is_valid:
        raise ValueError("The URL does not have a valid domain")

    if not domain.is_public:
        raise ValueError("The URL is not public")

    return True


def get_validator(schema_path):
    """Get a jsonschema validator object for a given schema path.

    :param schema_path: Path relative to the checkmate root
    """

    return Draft7Validator(
        json.load(resource_stream("checkmate", schema_path)),
        format_checker=_FORMAT_CHECKER,
    )


def get_validated_json_body(request, validator):
    """Get the JSON body of a request validated against a jsonschema

    :param request: Pyramid request object
    :param validator: A jsonschema validator (see `get_validator()`)
    :return: The json dict if validation is successful

    :raise MalformedJSONBody: If the JSON cannot be decoded or the body
        does not conform to the schema provided
    """

    try:
        body = request.json_body
    except ValueError as err:
        raise MalformedJSONBody(f"Posted JSON missing or malformed: {err}") from err

    try:
        validator.validate(body)
    except ValidationError as err:
        raise MalformedJSONBody(
            f"JSON body does not match expected schema: {err}"
        ) from err

    return body
