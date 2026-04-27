"""changed primary keys for parcelas and dispositivos. This makes more sense

Revision ID: 99bfd00b54c4
Revises: 66ab16e8c6c8
Create Date: 2026-04-27 09:57:26.175744

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99bfd00b54c4'
down_revision = '66ab16e8c6c8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('cultivo_parcela', schema=None) as batch_op:
        batch_op.alter_column(
            'parcela_id',
            existing_type=sa.String(50),
            type_=sa.Integer(),
            nullable=False
        )

    # 2. Crear FK en cultivo_parcela apuntando a parcelas.id
    with op.batch_alter_table('cultivo_parcela', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'cultivo_parcela_ibfk_2', 'parcelas', ['parcela_id'], ['id']
        )

    # 3. Añadir id en dispositivos
    with op.batch_alter_table('dispositivos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id', sa.Integer(), autoincrement=True, nullable=True))

def downgrade():
    with op.batch_alter_table('dispositivos', schema=None) as batch_op:
        batch_op.drop_column('id')

    with op.batch_alter_table('cultivo_parcela', schema=None) as batch_op:
        batch_op.drop_constraint('cultivo_parcela_ibfk_2', type_='foreignkey')
        batch_op.alter_column(
            'parcela_id',
            existing_type=sa.Integer(),
            type_=sa.String(50),
            nullable=False
        )

    with op.batch_alter_table('parcelas', schema=None) as batch_op:
        batch_op.drop_constraint('pk_parcelas', type_='primary')
        batch_op.create_primary_key('pk_parcelas', ['public_id'])
        batch_op.drop_column('id')