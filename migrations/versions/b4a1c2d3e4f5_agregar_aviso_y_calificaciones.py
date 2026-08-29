"""agregar aviso y calificaciones

Revision ID: a1b2c3d4e5f6
Revises: 19f7f775e336
Create Date: 2026-08-26 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '19f7f775e336'   # <--- Pon aquí el hash real de tu flask db current actual
branch_labels = None
depends_on = None


def upgrade():
    # Agregamos la columna a conductores
    with op.batch_alter_table('conductores', schema=None) as batch_op:
        batch_op.add_column(sa.Column('aviso_enviado', sa.Integer(), nullable=True, server_default='0'))

    # Agregamos las columnas a despachos
    with op.batch_alter_table('despachos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('calificacion', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('fecha_calificacion', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('comentario_calificacion', sa.Text(), nullable=True))


def downgrade():
    # Lógica para revertir en caso de un downgrade
    with op.batch_alter_table('despachos', schema=None) as batch_op:
        batch_op.drop_column('comentario_calificacion')
        batch_op.drop_column('fecha_calificacion')
        batch_op.drop_column('calificacion')

    with op.batch_alter_table('conductores', schema=None) as batch_op:
        batch_op.drop_column('aviso_enviado')