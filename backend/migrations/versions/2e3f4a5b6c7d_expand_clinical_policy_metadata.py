"""expand clinical policy metadata

Revision ID: 2e3f4a5b6c7d
Revises: 7c4f9d1a2e83
Create Date: 2026-07-14 08:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.core.db  # noqa: F401


revision: str = "2e3f4a5b6c7d"
down_revision: Union[str, None] = "7c4f9d1a2e83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    columns = _columns("clinical_policies")
    with op.batch_alter_table("clinical_policies", schema=None) as batch_op:
        if "name" not in columns:
            batch_op.add_column(sa.Column("name", sa.String(), nullable=False, server_default="rx_triage_default"))
        if "status" not in columns:
            batch_op.add_column(sa.Column("status", sa.String(), nullable=False, server_default="draft"))
        if "updated_at" not in columns:
            batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        if "activated_at" not in columns:
            batch_op.add_column(sa.Column("activated_at", sa.DateTime(), nullable=True))
        if "created_by_user_id" not in columns:
            batch_op.add_column(sa.Column("created_by_user_id", app.core.db.GUID(), nullable=True))
        if "notes" not in columns:
            batch_op.add_column(sa.Column("notes", sa.String(), nullable=True))

    columns = _columns("clinical_policies")
    with op.batch_alter_table("clinical_policies", schema=None) as batch_op:
        if "status" in columns:
            try:
                batch_op.create_index(batch_op.f("ix_clinical_policies_status"), ["status"], unique=False)
            except Exception:
                pass
        if "created_by_user_id" in columns:
            try:
                batch_op.create_foreign_key(
                    "fk_clinical_policies_created_by_user_id_users",
                    "users",
                    ["created_by_user_id"],
                    ["id"],
                )
            except Exception:
                pass

    bind = op.get_bind()
    bind.execute(sa.text(
        "UPDATE clinical_policies "
        "SET status = CASE WHEN active = 1 THEN 'active' ELSE 'draft' END "
        "WHERE status IS NULL OR status = 'draft'"
    ))
    bind.execute(sa.text(
        "UPDATE clinical_policies SET updated_at = created_at WHERE updated_at IS NULL"
    ))
    bind.execute(sa.text(
        "UPDATE clinical_policies SET activated_at = created_at "
        "WHERE active = 1 AND activated_at IS NULL"
    ))


def downgrade() -> None:
    columns = _columns("clinical_policies")
    with op.batch_alter_table("clinical_policies", schema=None) as batch_op:
        if "created_by_user_id" in columns:
            try:
                batch_op.drop_constraint("fk_clinical_policies_created_by_user_id_users", type_="foreignkey")
            except Exception:
                pass
        if "status" in columns:
            try:
                batch_op.drop_index(batch_op.f("ix_clinical_policies_status"))
            except Exception:
                pass
        for column in ["notes", "created_by_user_id", "activated_at", "updated_at", "status", "name"]:
            if column in columns:
                batch_op.drop_column(column)
