"""empty message

Revision ID: aeef37c779c1
Revises: 6436b82e452b
Create Date: 2022-11-24 17:32:54.009985

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aeef37c779c1'
down_revision = '6436b82e452b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('project_user', sa.Column('accepted_collaboration_invite', sa.Boolean(), nullable=True))
    op.execute('''UPDATE "project_user" SET accepted_collaboration_invite = false WHERE role!='owner'; ''')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('project_user', 'accepted_collaboration_invite')
    # ### end Alembic commands ###
