"""empty message

Revision ID: 36da442bc732
Revises: a030a3dbf194
Create Date: 2020-04-01 18:22:38.197341

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '36da442bc732'
down_revision = 'a030a3dbf194'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('project', sa.Column('description', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('project', 'description')
    # ### end Alembic commands ###
