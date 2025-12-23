"""crear tabla reservas con campo estado

Revision ID: 429647dc864f
Revises: c1234567890
Create Date: 2025-12-22 18:25:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '429647dc864f'
down_revision = 'c1234567890'
branch_labels = None
depends_on = None


def upgrade():
    # 🔹 Constraint con nombre explícito en conductores
    with op.batch_alter_table('conductores', schema=None) as batch_op:
        batch_op.create_unique_constraint("uq_conductores_codigo", ['codigo'])

    # 🔹 Crear tabla reservas si no existe
    op.create_table(
        'reservas',
        sa.Column('id_reserva', sa.Integer, primary_key=True),
        sa.Column('cliente_id', sa.Integer, sa.ForeignKey('clientes.id')),
        sa.Column('origen', sa.String(120)),
        sa.Column('destino', sa.String(120)),
        sa.Column('fecha', sa.Date),
        sa.Column('hora', sa.Time),
        sa.Column('estado', sa.String(20), nullable=True, server_default="activo")
    )


def downgrade():
    # 🔹 Eliminar constraint en conductores
    with op.batch_alter_table('conductores', schema=None) as batch_op:
        batch_op.drop_constraint("uq_conductores_codigo", type_="unique")

    # 🔹 Eliminar tabla reservas
    op.drop_table('reservas')
