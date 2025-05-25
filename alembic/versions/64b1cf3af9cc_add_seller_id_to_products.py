"""add seller_id to products

Revision ID: 64b1cf3af9cc
Revises: 5ecb1e6cd571
Create Date: 2025-05-25 17:25:46.090476

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64b1cf3af9cc'
down_revision: Union[str, None] = '5ecb1e6cd571'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
