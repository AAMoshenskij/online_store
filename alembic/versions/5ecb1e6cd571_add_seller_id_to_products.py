"""add seller_id to products

Revision ID: 5ecb1e6cd571
Revises: 1b3ee1dd87a0
Create Date: 2025-05-25 17:19:30.261953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ecb1e6cd571'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
