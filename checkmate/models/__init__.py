"""Data and domain models."""

from checkmate.models.db.allow_rule import AllowRule
from checkmate.models.db.custom_rule import CustomRule
from checkmate.models.db.url_haus_rule import URLHausRule
from checkmate.models.reason import Reason, Severity


def includeme(_config):  # pragma: no cover
    """Pyramid config."""

    # This is really only here to trigger loading of the SQLAlchemy classes so
    # they are registered correctly.
