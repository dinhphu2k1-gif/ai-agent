"""m1 admin identity columns + permission types

Revision ID: e9a1b2c3d400
Revises: d8f2a1c31000
Create Date: 2026-05-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e9a1b2c3d400"
down_revision: Union[str, Sequence[str], None] = "d8f2a1c31000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))
    op.add_column(
        "users",
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "roles",
        sa.Column("display_name", sa.String(length=255), nullable=True),
    )
    op.execute(
        sa.text("UPDATE roles SET display_name = name WHERE display_name IS NULL")
    )
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("roles") as batch_op:
            batch_op.alter_column("display_name", nullable=False)
    else:
        op.alter_column("roles", "display_name", nullable=False)
    op.add_column("groups", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("groups", "description")
    op.drop_column("roles", "display_name")
    op.drop_column("users", "last_active_at")
    op.drop_column("users", "full_name")
