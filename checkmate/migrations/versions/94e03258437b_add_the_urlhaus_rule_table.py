"""Add the urlhaus_rule table.

Revision ID: 94e03258437b
Revises:
Create Date: 2020-12-11 17:51:36.741186

"""

# pylint:disable=invalid-name,no-member
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "94e03258437b"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "urlhaus_rule",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("hash", sa.String(collation="C"), nullable=False, index=True),
        sa.Column("rule", sa.String, nullable=False),
    )


def downgrade():
    op.drop_table("urlhaus_rule")
