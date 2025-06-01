import time
from elasticsearch import AsyncElasticsearch, exceptions as es_exceptions
import os
from elasticsearch.exceptions import ConnectionError, RequestError, TransportError
from apps.core.metrics import ES_REQUESTS_TOTAL, ES_REQUEST_DURATION_SECONDS, ES_INDEXING_DOCUMENTS_TOTAL

class InstrumentedAsyncElasticsearch:
    def __init__(self, es_client: AsyncElasticsearch):
        self._client = es_client

    async def _execute_es_call(self, es_operation_func, operation_name: str, index_name: str = "_all", *args, **kwargs):
        start_time = time.time()
        status = "success"
        try:
            response = await es_operation_func(*args, **kwargs)
            if operation_name == "index" and kwargs.get('document'):
                ES_INDEXING_DOCUMENTS_TOTAL.labels(index=index_name).inc()
            elif operation_name == "bulk" and kwargs.get('operations'):
                op_count = 0
                indices = set()
                for op in kwargs.get('operations', []):
                    if isinstance(op, dict): 
                        action = list(op.keys())[0] 
                        if action in ["index", "create", "update"]:
                            op_count+=1
                            indices.add(op[action].get("_index", index_name))
                if op_count > 0: 
                    for idx in indices: 
                         ES_INDEXING_DOCUMENTS_TOTAL.labels(index=idx).inc(op_count / len(indices) if indices else 1) 
            return response
        except es_exceptions.ElasticsearchException as e:
            status = "error"
            raise e 
        finally:
            duration = time.time() - start_time
            ES_REQUEST_DURATION_SECONDS.labels(operation=operation_name, index=index_name).observe(duration)
            ES_REQUESTS_TOTAL.labels(operation=operation_name, index=index_name, status=status).inc()

    async def search(self, index="_all", **kwargs):
        effective_index = index
        if isinstance(index, (list, tuple)):
            effective_index = ",".join(index) if index else "_all" 
        elif index is None: 
            effective_index = "_all"

        return await self._execute_es_call(self._client.search, "search", effective_index, index=index, **kwargs)

    async def index(self, index, document, **kwargs):
        
        return await self._execute_es_call(self._client.index, "index", index, index=index, document=document, **kwargs)

    async def get(self, index, id, **kwargs):
        return await self._execute_es_call(self._client.get, "get", index, index=index, id=id, **kwargs)

    async def delete(self, index, id, **kwargs):
        return await self._execute_es_call(self._client.delete, "delete", index, index=index, id=id, **kwargs)
        
    async def bulk(self, operations, index=None, **kwargs):
        
        
        
        
        effective_index = index if index else "_bulk_operation"
        return await self._execute_es_call(self._client.bulk, "bulk", effective_index, operations=operations, index=index, **kwargs)

    async def ping(self, **kwargs):
        
        return await self._execute_es_call(self._client.ping, "ping", "_internal", **kwargs)

    async def close(self):
        await self._client.close()

    
    



