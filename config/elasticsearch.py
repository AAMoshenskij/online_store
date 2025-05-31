from elasticsearch import AsyncElasticsearch
import os

host = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
port = os.getenv("ELASTICSEARCH_PORT", "9200")

es = AsyncElasticsearch(
    hosts=[f"http://{host}:{port}"],
    timeout=30,
    max_retries=3,
    retry_on_timeout=True
)

async def check_connection():
    try:
        if not await es.ping():
            raise ConnectionError("Не удалось подключиться к Elasticsearch")
        print("Подключение к Elasticsearch успешно")
    except Exception as e:
        print(f"! Ошибка подключения к Elasticsearch: {e}")