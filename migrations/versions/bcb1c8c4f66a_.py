"""empty message

Revision ID: bcb1c8c4f66a
Revises: 80df49665332
Create Date: 2022-09-01 05:06:35.769063

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bcb1c8c4f66a'
down_revision = '80df49665332'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('billing_invoices', sa.Column('display_id', sa.String(), server_default=sa.text("concat('CC',to_char(CURRENT_DATE, 'YY'), '-', substring(uuid_generate_v4()::TEXT from 1 for 8))"), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('billing_invoices', 'display_id')
    # ### end Alembic commands ###
