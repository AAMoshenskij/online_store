"""add_sellers_table

Revision ID: a6cd261da94b
Revises: 
Create Date: 2025-05-23 18:44:52.556038

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6cd261da94b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('products', sa.Column('seller_id', sa.Integer(), nullable=False))
    op.create_foreign_key('fk_product_seller', 'products', 'sellers', ['seller_id'], ['id'])

def downgrade():
    op.drop_constraint('fk_product_seller', 'products', type_='foreignkey')
    op.drop_column('products', 'seller_id')
