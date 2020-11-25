"""Model for our own blocking rules."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from checkmate.db import BASE


class CustomRule(BASE):
    """Rule about blocking a particular resource."""

    __tablename__ = "custom_rule"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    rule = sa.Column(sa.String, nullable=False)
    """The text of the rule"""

    hash = sa.Column(sa.String, nullable=False)
    """A hash for quick comparison"""

    reasons = sa.Column(ARRAY(sa.Integer, dimensions=1))
    """The list of reasons why we are blocking this"""
