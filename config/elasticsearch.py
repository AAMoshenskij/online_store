from elasticsearch import AsyncElasticsearch
import os
# Use the instrumented client
from .instrumented_elasticsearch import InstrumentedAsyncElasticsearch

_raw_es_client = AsyncElasticsearch(
    hosts=[os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")],
    timeout=30,
    max_retries=3,
    retry_on_timeout=True
)

# es is now an instance of our instrumented client
es = InstrumentedAsyncElasticsearch(es_client=_raw_es_client)

async def check_connection():
    try:
        # Use the instrumented client's ping method
        if not await es.ping(): 
            raise ConnectionError("Не удалось подключиться к Elasticsearch")
        print("✓ Подключение к Elasticsearch успешно")
    except Exception as e:
        print(f"! Ошибка подключения к Elasticsearch: {e}")