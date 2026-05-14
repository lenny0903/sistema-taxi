"""agregando campos de exoneracion y categorias

Revision ID: 70f723c0aa23
Revises: 
Create Date: 2026-05-13 12:05:17.135075

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70f723c0aa23'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Con batch_alter_table para evitar problemas en SQLite
    with op.batch_alter_table('cuotas_semanales', schema=None) as batch_op:
        batch_op.add_column(sa.Column('es_exonerado', sa.Boolean(), server_default='0', nullable=True))
        # CORRECCIÓN AQUÍ: sa.Column('nombre', tipo)
        batch_op.add_column(sa.Column('tipo_novedad', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('observaciones', sa.Text(), nullable=True))

    with op.batch_alter_table('pagos_cuotas', schema=None) as batch_op:
        batch_op.add_column(sa.Column('es_exoneracion', sa.Boolean(), server_default='0', nullable=True))
        # CORRECCIÓN AQUÍ: sa.Column('nombre', tipo)
        batch_op.add_column(sa.Column('tipo_incidencia', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('observaciones', sa.Text(), nullable=True))
def downgrade():
    with op.batch_alter_table('pagos_cuotas', schema=None) as batch_op:
        batch_op.drop_column('observaciones')
        batch_op.drop_column('tipo_incidencia')
        batch_op.drop_column('es_exoneracion')

    with op.batch_alter_table('cuotas_semanales', schema=None) as batch_op:
        batch_op.drop_column('observaciones')
        batch_op.drop_column('tipo_novedad')
        batch_op.drop_column('es_exonerado')
