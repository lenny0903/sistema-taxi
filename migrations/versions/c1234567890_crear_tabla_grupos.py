"""crear tabla grupos

Revision ID: c1234567890
Revises: b001b54b64f1
Create Date: 2025-12-21 01:20:00
"""
from alembic import op
import sqlalchemy as sa

# Identificadores de revisión
revision = 'c1234567890'
down_revision = 'b001b54b64f1'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'grupos',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('grupo_id', sa.String(length=50), unique=True, nullable=False),
        sa.Column('cliente', sa.String(length=100), nullable=False),
        sa.Column('telefono', sa.String(length=20), nullable=False),
        sa.Column('origen', sa.String(length=200), nullable=False),
        sa.Column('destino', sa.String(length=200), nullable=False),
        sa.Column('tarifa', sa.Float(), nullable=False),
        sa.Column('num_autos', sa.Integer(), nullable=False)
    )

def downgrade():
    op.drop_table('grupos')
