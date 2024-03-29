"""empty message

Revision ID: 3dd1aeef7d33
Revises: 9105e64cc3c2
Create Date: 2023-07-26 12:34:49.295327

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3dd1aeef7d33'
down_revision = '9105e64cc3c2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('app', sa.Column('private_image', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('app', 'private_image')
    # ### end Alembic commands ###
