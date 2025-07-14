"""add_relates_to_clean_data_nature_protocol

Revision ID: 58ac8ca8bb76
Revises: 6836d2ab85c8
Create Date: 2024-10-10 14:57:23.635286

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '58ac8ca8bb76'
down_revision = '6836d2ab85c8'
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table('clean_data_nature_protocol', schema=None) as batch_op:
        batch_op.add_column(sa.Column('relates', sa.JSON(), nullable=True))


    # ### end Alembic commands ###


def downgrade():


    with op.batch_alter_table('clean_data_nature_protocol', schema=None) as batch_op:

        batch_op.drop_column('relates')

