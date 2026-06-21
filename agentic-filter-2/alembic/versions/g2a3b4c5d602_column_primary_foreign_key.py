"""columns.is_primary_key and is_foreign_key (wizard tree metadata)

Revision ID: g2a3b4c5d602
Revises: f1a2b3c4d501
Create Date: 2026-05-20

Schema review S5 — replaces name heuristics when values are set.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g2a3b4c5d602"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d501"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "columns",
        sa.Column("is_primary_key", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "columns",
        sa.Column("is_foreign_key", sa.Boolean(), nullable=True),
    )

    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE columns
            SET is_primary_key = TRUE
            WHERE lower(name) IN ('id', 'event_id')
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE columns
            SET is_foreign_key = TRUE
            WHERE lower(name) LIKE '%\\_id' ESCAPE '\\'
              AND lower(name) NOT IN ('id', 'event_id')
            """
        )
    )


def downgrade() -> None:
    op.drop_column("columns", "is_foreign_key")
    op.drop_column("columns", "is_primary_key")
