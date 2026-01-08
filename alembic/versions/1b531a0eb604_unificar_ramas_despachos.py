"""Unificar ramas despachos

Revision ID: 1b531a0eb604
Revises: 7cc0e9aab701, a682f0bb7cd2
Create Date: 2026-01-07 01:17:48.412972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b531a0eb604'
down_revision: Union[str, Sequence[str], None] = ('7cc0e9aab701', 'a682f0bb7cd2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
