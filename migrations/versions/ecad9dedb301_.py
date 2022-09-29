"""empty message

Revision ID: ecad9dedb301
Revises: 8f6e75f2412c
Create Date: 2022-09-28 23:41:22.518287

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ecad9dedb301'
down_revision = '8f6e75f2412c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('project_user', 'project_id',
               existing_type=postgresql.UUID(),
               nullable=False)
    op.alter_column('project_user', 'user_id',
               existing_type=postgresql.UUID(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('project_user', 'user_id',
               existing_type=postgresql.UUID(),
               nullable=True)
    op.alter_column('project_user', 'project_id',
               existing_type=postgresql.UUID(),
               nullable=True)
    # ### end Alembic commands ###
