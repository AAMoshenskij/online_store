"""add column to products

Revision ID: 68838ef733ef
Revises: a0be4e81f8ab
Create Date: 2025-05-25 17:53:25.737986

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68838ef733ef'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# в созданном файле миграции
def upgrade():
    # 1. Добавляем колонку с NULL
    op.add_column('products', sa.Column('seller_id', sa.Integer(), nullable=True))
    
    # 2. НАЧАЛО: Обновляем все существующие записи, чтобы иметь значение seller_id
    # Этот код нужно выполнить вручную внутри миграции, например через execute():
    op.execute("UPDATE products SET seller_id = 1 WHERE seller_id IS NULL")  # или другое значение
    
    # 3. Делает колонку обязательной
    op.alter_column('products', 'seller_id', nullable=False)

def downgrade():
    op.drop_constraint('fk_product_seller', 'products', type_='foreignkey')
    op.drop_column('products', 'seller_id')