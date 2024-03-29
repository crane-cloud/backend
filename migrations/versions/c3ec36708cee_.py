"""empty message

Revision ID: c3ec36708cee
Revises: 069455f983d0
Create Date: 2022-04-20 20:31:16.553523

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3ec36708cee'
down_revision = '069455f983d0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('transaction_record_email_key', 'transaction_record', type_='unique')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('transaction_record_email_key', 'transaction_record', ['email'])
    # ### end Alembic commands ###
