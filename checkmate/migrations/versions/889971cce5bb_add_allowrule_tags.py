"""Add AllowRule.tags.

Revision ID: 889971cce5bb
Revises: da834231662a
Create Date: 2021-01-11 15:14:14.351656

"""
# pylint:disable=invalid-name,no-member
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY

revision = "889971cce5bb"
down_revision = "da834231662a"


def upgrade():
    op.add_column(
        "allow_rule",
        sa.Column(
            "tags", ARRAY(sa.String, dimensions=1), server_default="{}", nullable=False
        ),
    )


def downgrade():
    op.drop_column("allow_rule", "tags")
