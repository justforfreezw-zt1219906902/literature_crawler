"""add_fail_reason_to_task

Revision ID: ebf4ab29b6a2
Revises: a2151aa3934c
Create Date: 2024-10-11 15:59:53.951784

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ebf4ab29b6a2'
down_revision = 'a2151aa3934c'
branch_labels = None
depends_on = None


def upgrade():


    with op.batch_alter_table('datasets_task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('failed_reason', sa.String(length=1024), nullable=True))



    # ### end Alembic commands ###


def downgrade():


    with op.batch_alter_table('datasets_task', schema=None) as batch_op:
        batch_op.drop_column('failed_reason')


