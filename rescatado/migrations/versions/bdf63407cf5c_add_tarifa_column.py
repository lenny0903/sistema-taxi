"""add tarifa column

Revision ID: bdf63407cf5c
Revises: e13002087902
Create Date: 2025-12-05 11:10:33.339870
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'bdf63407cf5c'
down_revision = 'e13002087902'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('lista_espera', sa.Column('tarifa', sa.Float(), nullable=True))

def downgrade():
    op.drop_column('lista_espera', 'tarifa')

    pass
