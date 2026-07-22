"""Add grupo_id to despachos

Revision ID: ae123606445a
Revises: ab8ec844675c
Create Date: 2025-12-20 23:41:39.143678
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ae123606445a'
down_revision = 'ab8ec844675c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('despachos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('grupo_id', sa.String(length=50), nullable=True))
        batch_op.create_index('ix_despachos_grupo_id', ['grupo_id'], unique=False)


def downgrade():
    with op.batch_alter_table('despachos', schema=None) as batch_op:
        batch_op.drop_index('ix_despachos_grupo_id')
        batch_op.drop_column('grupo_id')
