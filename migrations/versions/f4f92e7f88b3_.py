"""empty message

Revision ID: f4f92e7f88b3
Revises: 08246b2fe16f
Create Date: 2022-04-20 10:47:21.797476

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f4f92e7f88b3'
down_revision = '08246b2fe16f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('transaction_record',
    sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=True),
    sa.Column('currency', sa.String(length=256), nullable=True),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.Column('email', sa.String(length=256), nullable=True),
    sa.Column('phone_number', sa.String(length=256), nullable=True),
    sa.Column('flutterwave_ref', sa.String(length=256), nullable=True),
    sa.Column('status', sa.String(length=256), nullable=True),
    sa.Column('tx_ref', sa.String(length=256), nullable=True),
    sa.Column('transaction_id', sa.Integer(), nullable=True),
    sa.Column('date_created', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transaction_record')
    # ### end Alembic commands ###