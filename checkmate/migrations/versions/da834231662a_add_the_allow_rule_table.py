"""Add the allow_rule table.

Revision ID: da834231662a
Revises: 94e03258437b
Create Date: 2021-01-08 13:17:37.947693

"""

# pylint:disable=invalid-name,no-member
import sqlalchemy as sa
from alembic import op

revision = "da834231662a"
down_revision = "94e03258437b"


def upgrade():
    op.create_table(
        "allow_rule",
        sa.Column("id", sa.Integer, autoincrement=True, primary_key=True),
        sa.Column("hash", sa.String(collation="C"), nullable=False, index=True),
        sa.Column("rule", sa.String, nullable=False, unique=True),
        sa.Column(
            "force",
            sa.Boolean,
            nullable=False,
            server_default=(sa.sql.expression.false()),
        ),
    )


def downgrade():
    op.drop_table("allow_rule")
