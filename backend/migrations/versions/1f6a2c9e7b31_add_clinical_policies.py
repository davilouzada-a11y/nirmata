"""add clinical policies

Revision ID: 1f6a2c9e7b31
Revises: ba09a90b3bf6
Create Date: 2026-07-12 10:52:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.core.db  # noqa: F401


revision: str = "1f6a2c9e7b31"
down_revision: Union[str, None] = "ba09a90b3bf6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "clinical_policies" in inspector.get_table_names():
        return

    op.create_table(
        "clinical_policies",
        sa.Column("id", app.core.db.GUID(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("rules", sa.JSON(), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False),
        sa.Column("autonomous_diagnosis_allowed", sa.Boolean(), nullable=False),
        sa.Column("finalization_rule", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version"),
    )
    with op.batch_alter_table("clinical_policies", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_clinical_policies_active"), ["active"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "clinical_policies" not in inspector.get_table_names():
        return

    with op.batch_alter_table("clinical_policies", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_clinical_policies_active"))
    op.drop_table("clinical_policies")
