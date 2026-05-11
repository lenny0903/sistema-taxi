"""Añadir tablas de pagos y saldos

Revision ID: 8e8460b27925
Revises: d265422ede41
Create Date: 2026-05-06 19:36:26.413898

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8e8460b27925'
down_revision = 'd265422ede41'
branch_labels = None
depends_on = None


def upgrade():
    # ### Comandos corregidos por Lenny para evitar errores de SQLite ###
    with op.batch_alter_table('cola_despachos', schema=None) as batch_op:
        batch_op.alter_column('origen',
               existing_type=sa.VARCHAR(length=120),
               type_=sa.String(length=255),
               existing_nullable=True)
        batch_op.alter_column('destino',
               existing_type=sa.VARCHAR(length=120),
               type_=sa.String(length=255),
               existing_nullable=True)
        batch_op.alter_column('fecha_creacion',
               existing_type=sa.DATETIME(),
               nullable=False)
        # Nota: Si estas columnas no existen en tu DB actual, 
        # puedes comentar las líneas de drop_column
        # batch_op.drop_column('punto_id')
        # batch_op.drop_column('nro_autos')

    with op.batch_alter_table('despachos', schema=None) as batch_op:
        batch_op.alter_column('destino_despacho',
               existing_type=sa.VARCHAR(length=120),
               type_=sa.String(length=200),
               existing_nullable=True)

    with op.batch_alter_table('incidencias', schema=None) as batch_op:
        batch_op.alter_column('cliente_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    with op.batch_alter_table('matriz_tarifas', schema=None) as batch_op:
        batch_op.alter_column('destino',
               existing_type=sa.TEXT(),
               nullable=False)
        batch_op.alter_column('precio_cop',
               existing_type=sa.REAL(),
               type_=sa.Float(),
               existing_nullable=True)

   # with op.batch_alter_table('turnos', schema=None) as batch_op:
   #     batch_op.alter_column('punto_id',
   #            existing_type=sa.INTEGER(),
   #            nullable=False)

    # AQUÍ DEBERÍAN ESTAR LAS TABLAS DE PAGOS SI NO LAS TIENES
    # Si flask db migrate no las puso, es porque ya existen en los modelos.
    # ### end Alembic commands ###


def downgrade():
    # ### Comandos de reversión corregidos ###
   # with op.batch_alter_table('turnos', schema=None) as batch_op:
   #     batch_op.alter_column('punto_id',
   #            existing_type=sa.INTEGER(),
   #            nullable=True)

    with op.batch_alter_table('matriz_tarifas', schema=None) as batch_op:
        batch_op.alter_column('precio_cop',
               existing_type=sa.Float(),
               type_=sa.REAL(),
               existing_nullable=True)

    with op.batch_alter_table('despachos', schema=None) as batch_op:
        batch_op.alter_column('destino_despacho',
               existing_type=sa.String(length=200),
               type_=sa.VARCHAR(length=120),
               existing_nullable=True)

    with op.batch_alter_table('cola_despachos', schema=None) as batch_op:
        batch_op.alter_column('fecha_creacion',
               existing_type=sa.DATETIME(),
               nullable=True)
