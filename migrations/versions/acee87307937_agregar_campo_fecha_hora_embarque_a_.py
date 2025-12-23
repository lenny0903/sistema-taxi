from alembic import op
import sqlalchemy as sa


# Identificadores de la migración
revision = 'acee87307937'
down_revision = 'e13002087902'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('despachos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fecha_hora_embarque', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('despachos', schema=None) as batch_op:
        batch_op.drop_column('fecha_hora_embarque')

