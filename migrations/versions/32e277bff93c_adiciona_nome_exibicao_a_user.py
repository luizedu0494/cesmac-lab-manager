"""Adiciona nome_exibicao a User

Revision ID: 32e277bff93c
Revises: 0f1429210246
Create Date: 2025-06-18 00:39:42.257146

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32e277bff93c'
down_revision = '0f1429210246'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nome_exibicao', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('nome_exibicao')

    # ### end Alembic commands ###
