"""empty message

Revision ID: 9e5db6c0d658
Revises: 7e99f2d0d477
Create Date: 2023-04-26 19:48:38.803196

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e5db6c0d658'
down_revision = '7e99f2d0d477'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('project', sa.Column('admin_disabled', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('project', 'admin_disabled')
    # ### end Alembic commands ###