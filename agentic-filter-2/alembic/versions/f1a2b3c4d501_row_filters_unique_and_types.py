"""row_filters unique per permission; permission_types DESCRIBE; effect CHECK

Revision ID: f1a2b3c4d501
Revises: e9a1b2c3d400
Create Date: 2026-05-20

Phase 0 (Add Permission wizard): migration S1 + S2 + seed type DESCRIBE.
"""

from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d501"
down_revision: Union[str, Sequence[str], None] = "e9a1b2c3d400"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DESCRIBE_PERMISSION_TYPE_ID = UUID("44444444-4444-4444-8444-444444444444")


def _dedupe_row_filters(bind) -> None:
    if bind.dialect.name == "postgresql":
        op.execute(
            sa.text(
                """
                DELETE FROM row_filters rf
                WHERE rf.id IN (
                    SELECT id FROM (
                        SELECT id,
                               ROW_NUMBER() OVER (
                                   PARTITION BY permission_id ORDER BY id
                               ) AS rn
                        FROM row_filters
                    ) ranked
                    WHERE rn > 1
                )
                """
            )
        )
    else:
        op.execute(
            sa.text(
                """
                DELETE FROM row_filters
                WHERE id NOT IN (
                    SELECT MIN(id) FROM row_filters GROUP BY permission_id
                )
                """
            )
        )


def upgrade() -> None:
    bind = op.get_bind()
    _dedupe_row_filters(bind)

    op.create_unique_constraint(
        "uq_row_filters_permission_id",
        "row_filters",
        ["permission_id"],
    )

    op.create_check_constraint(
        "ck_permissions_effect",
        "permissions",
        "effect IN ('ALLOW', 'DENY')",
    )

    insert_describe = sa.text(
        "INSERT INTO permission_types (id, name) VALUES (:id, 'DESCRIBE')"
    ).bindparams(id=DESCRIBE_PERMISSION_TYPE_ID)
    if bind.dialect.name == "postgresql":
        op.execute(
            sa.text(
                """
                INSERT INTO permission_types (id, name)
                VALUES (:id, 'DESCRIBE')
                ON CONFLICT (name) DO NOTHING
                """
            ).bindparams(id=DESCRIBE_PERMISSION_TYPE_ID)
        )
    else:
        op.execute(insert_describe)


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_constraint("ck_permissions_effect", "permissions", type_="check")
    op.drop_constraint("uq_row_filters_permission_id", "row_filters", type_="unique")

    if bind.dialect.name == "postgresql":
        op.execute(
            sa.text("DELETE FROM permission_types WHERE name = 'DESCRIBE'")
        )
    else:
        op.execute(
            sa.text("DELETE FROM permission_types WHERE name = 'DESCRIBE'")
        )
