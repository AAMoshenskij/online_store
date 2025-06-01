#!/usr/bin/env python3
import asyncio
from config.elasticsearch import es

async def create_products_index():
    """Создание индекса для товаров если он не существует"""
    index_name = "products"
    
    if not await es.indices.exists(index=index_name):
        await es.indices.create(
            index=index_name,
            body={
                "mappings": {
                    "properties": {
                        "name": {"type": "text", "analyzer": "standard"},
                        "description": {"type": "text"},
                        "category": {"type": "keyword"},
                        "price": {"type": "float"},
                        "seller_id": {"type": "integer"},
                        "stock": {"type": "integer"},
                        "rating": {"type": "float"},
                        "created_at": {"type": "date"},
                        "attributes": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"},
                                "value": {"type": "keyword"}
                            }
                        }
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                }
            }
        )
        print(f"✓ Индекс '{index_name}' успешно создан")
    else:
        print(f"Индекс '{index_name}' уже существует")

async def main():
    try:
        await create_products_index()
    finally:
        await es.close()

if __name__ == "__main__":
    asyncio.run(main())