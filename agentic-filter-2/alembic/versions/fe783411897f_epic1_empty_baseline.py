"""epic1_empty_baseline

Revision ID: fe783411897f
Revises: 
Create Date: 2026-05-14 10:53:29.616154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'fe783411897f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
