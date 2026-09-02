"""agregar columna tarifa a cola_despachos

Revision ID: 187f89723772
Revises: a1b2c3d4e5f6
Create Date: 2026-09-02 02:22:08.205386

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '187f89723772'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('cola_despachos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tarifa', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'))


def downgrade():
    with op.batch_alter_table('cola_despachos', schema=None) as batch_op:
        batch_op.drop_column('tarifa')
