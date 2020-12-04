"""Data and domain models."""

from checkmate.models.data.custom_rule import CustomRule


def includeme(_config):  # pragma: no cover
    """Pyramid config."""

    # This is really only here to trigger loading of the SQLAlchemy classes so
    # they are registered correctly.
