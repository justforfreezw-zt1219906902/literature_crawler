"""add_file_info_to_clean_data_protocol_io

Revision ID: a51e5fa201b1
Revises: ebf4ab29b6a2
Create Date: 2024-10-11 18:21:02.744381

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a51e5fa201b1'
down_revision = 'ebf4ab29b6a2'
branch_labels = None
depends_on = None


def upgrade():


    with op.batch_alter_table('clean_data_protocol_io', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_info', sa.JSON(), nullable=True))




def downgrade():


    with op.batch_alter_table('clean_data_protocol_io', schema=None) as batch_op:
        batch_op.drop_column('file_info')


