"""add policy version to reviews

Revision ID: 7c4f9d1a2e83
Revises: 1f6a2c9e7b31
Create Date: 2026-07-12 11:18:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c4f9d1a2e83"
down_revision: Union[str, None] = "1f6a2c9e7b31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("reviews")}
    if "clinical_policy_version" in columns:
        return

    with op.batch_alter_table("reviews", schema=None) as batch_op:
        batch_op.add_column(sa.Column("clinical_policy_version", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("reviews")}
    if "clinical_policy_version" not in columns:
        return

    with op.batch_alter_table("reviews", schema=None) as batch_op:
        batch_op.drop_column("clinical_policy_version")
