"""Model for our own allow rules."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from checkmate.db import BASE
from checkmate.models.db.mixins import HashMatchMixin, JSONAPIMixin


class AllowRule(BASE, HashMatchMixin, JSONAPIMixin):
    """Rule about allowing a particular resource."""

    BULK_UPSERT_INDEX_ELEMENTS = ["rule"]
    BULK_UPSERT_UPDATE_ELEMENTS = ["hash"]

    __tablename__ = "allow_rule"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    hash = HashMatchMixin.hash_column()
    """A hash for quick comparison."""

    # While our hashes should be unique, we might change our mind about how
    # we hash. The rule itself should stay the same
    rule = sa.Column(sa.String, nullable=False, unique=True)
    """The text of the rule"""

    # If there is a conflict with a blocking rule, should this allow take
    # precedence?
    force = sa.Column(
        sa.Boolean, nullable=False, server_default=(sa.sql.expression.false())
    )

    tags = sa.Column(
        ARRAY(sa.String, dimensions=1), server_default="{}", nullable=False
    )
    """A list of tags documenting where this rule came from."""
