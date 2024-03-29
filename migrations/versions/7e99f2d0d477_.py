"""empty message

Revision ID: 7e99f2d0d477
Revises: 7a5c2b49d0a8
Create Date: 2023-03-16 23:06:48.124595

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e99f2d0d477'
down_revision = '7a5c2b49d0a8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('project', sa.Column('disabled', sa.Boolean(), nullable=True))
    op.add_column('project_database', sa.Column('disabled', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('project_database', 'disabled')
    op.drop_column('project', 'disabled')
    # ### end Alembic commands ###
