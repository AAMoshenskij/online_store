from elasticsearch import AsyncElasticsearch
import os

es = AsyncElasticsearch(
    hosts=[os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")],
    timeout=30,
    max_retries=3,
    retry_on_timeout=True
)

async def check_connection():
    try:
        if not await es.ping():
            raise ConnectionError("Не удалось подключиться к Elasticsearch")
        print("✓ Подключение к Elasticsearch успешно")
    except Exception as e:
        print(f"! Ошибка подключения к Elasticsearch: {e}")