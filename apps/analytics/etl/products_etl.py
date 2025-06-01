# apps/analytics/etl/products_etl.py
import pandas as pd
from sqlalchemy import create_engine
from config.settings import DATABASES

def load_products_from_csv():
    df = pd.read_csv('products.csv')
    
    # Преобразование данных под вашу модель
    df_clean = df.rename(columns={
        'name': 'product_name',
        'link': 'external_link',
        'image': 'external_image_url',
        'ratings': 'external_ratings',
        'no_of_ratings': 'external_ratings_count',
        'actual_price': 'external_price',
        'discount_price': 'external_discount_price'
    })
    
    # Очистка числовых полей (например, "30,227" -> 30227)
    df_clean['external_ratings_count'] = df_clean['external_ratings_count'].str.replace(',', '').astype(int)
    
    # Загрузка в PostgreSQL
    engine = create_engine(DATABASES["url"])
    df_clean.to_sql('products', engine, if_exists='append', index=False)

from config.elasticsearch import es
from config.database import DatabaseManager
from apps.products.models import Product, ProductVariant
from sqlalchemy.orm import joinedload
import asyncio

async def sync_products_to_elasticsearch():
    with DatabaseManager.session as session:
        # Загружаем продукты вместе с вариантами и медиа
        products = session.query(Product).options(
            joinedload(Product.variants),
            joinedload(Product.media)
        ).all()
        
        for product in products:
            # Основные данные продукта
            doc = {
                "id": product.id,
                "name": product.product_name,
                "description": product.description or "",
                "status": product.status,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "price": product.variants[0].price if product.variants else 0,
                "stock": product.variants[0].stock if product.variants else 0,
                "rating": 4.5,  # Заглушка, замените на реальные данные из отзывов
                "category": "general",  # Замените на реальную категорию
                "image_url": product.media[0].src if product.media else None
            }
            
            # Добавляем в Elasticsearch
            await es.index(
                index="products",
                id=product.id,
                body=doc
            )
        
        print(f"✓ Синхронизировано {len(products)} товаров в Elasticsearch")