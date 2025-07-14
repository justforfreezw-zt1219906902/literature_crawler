"""add_paper_type_to_clean_data_nature_protocol

Revision ID: 6836d2ab85c8
Revises: 8b13ea4e86db
Create Date: 2024-10-09 19:06:20.297817

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6836d2ab85c8'
down_revision = '8b13ea4e86db'
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table('clean_data_nature_protocol', schema=None) as batch_op:
        batch_op.add_column(sa.Column('paper_type', sa.String(length=255), nullable=True))




    # ### end Alembic commands ###


def downgrade():


    with op.batch_alter_table('clean_data_nature_protocol', schema=None) as batch_op:

        batch_op.drop_column('paper_type')


    # ### end Alembic commands ###
