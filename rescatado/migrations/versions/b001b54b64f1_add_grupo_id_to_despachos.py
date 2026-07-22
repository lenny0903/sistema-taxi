"""Add grupo_id to despachos

Revision ID: b001b54b64f1
Revises: ae123606445a
Create Date: 2025-12-20 23:48:24.338104
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b001b54b64f1'
down_revision = 'ae123606445a'
branch_labels = None
depends_on = None


def upgrade():
    # Añadir columna grupo_id a despachos
    with op.batch_alter_table('despachos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('grupo_id', sa.String(length=50), nullable=True))
        batch_op.create_foreign_key(
            'fk_despachos_grupo_id',   # nombre explícito
            'grupos',                  # tabla referenciada
            ['grupo_id'],              # columna local
            ['grupo_id']               # columna remota
        )


def downgrade():
    # Eliminar columna y constraint
    with op.batch_alter_table('despachos', schema=None) as batch_op:
        batch_op.drop_constraint('fk_despachos_grupo_id', type_='foreignkey')
        batch_op.drop_column('grupo_id')
