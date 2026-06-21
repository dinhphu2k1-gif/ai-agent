"""access_logs decision + request_id (Epic 8 audit)

Revision ID: d8f2a1c31000
Revises: cfeb49a5c688
Create Date: 2026-05-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d8f2a1c31000"
down_revision: Union[str, Sequence[str], None] = "cfeb49a5c688"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "access_logs",
        sa.Column("decision", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "access_logs",
        sa.Column("request_id", sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("access_logs", "request_id")
    op.drop_column("access_logs", "decision")
