"""Eliminar columna destino_despacho de despachos

Revision ID: a682f0bb7cd2
Revises: 7cc0e9aab701
Create Date: 2026-01-07 01:03:42.487004
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a682f0bb7cd2'
down_revision: Union[str, Sequence[str], None] = '7cc0e9aab701'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: eliminar columna destino_despacho."""
    with op.batch_alter_table("despachos", schema=None) as batch_op:
        batch_op.drop_column("destino_despacho")


def downgrade() -> None:
    """Downgrade schema: restaurar columna destino_despacho."""
    with op.batch_alter_table("despachos", schema=None) as batch_op:
        batch_op.add_column(sa.Column("destino_despacho", sa.String(length=100), nullable=True))

