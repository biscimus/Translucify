"""fix event log type

Revision ID: 1723922205
Revises: 1723922074
Create Date: 2024-08-17 21:16:45.298852

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1723922205'
down_revision: Union[str, None] = '1723922074'
branch_labels: Union[str, Sequence[str], None] = ()
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('log', 'type',
               existing_type=sa.VARCHAR(length=16),
               type_=sa.Enum('CSV', 'XES', name='eventlogtype'),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('log', 'type',
               existing_type=sa.Enum('CSV', 'XES', name='eventlogtype'),
               type_=sa.VARCHAR(length=16),
               existing_nullable=False)
    # ### end Alembic commands ###
