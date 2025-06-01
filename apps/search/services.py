from config.elasticsearch import es
from fastapi import HTTPException
from typing import List, Dict

async def search_products(
    query: str, 
    category: str = None, 
    min_rating: float = None
) -> List[Dict]:
    try:
        # Базовый запрос
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name^3", "description", "category^2"]
                            }
                        }
                    ],
                    "filter": []
                }
            },
            "size": 100  # Лимит результатов
        }

        # Добавляем фильтры
        if category:
            search_body["query"]["bool"]["filter"].append(
                {"term": {"category.keyword": category}}
            )
        if min_rating:
            search_body["query"]["bool"]["filter"].append(
                {"range": {"rating": {"gte": min_rating}}}
            )

        # Выполняем асинхронный запрос
        response = await es.search(
            index="products",
            body=search_body
        )

        # Форматируем результаты
        return [
            {
                **hit["_source"],
                "score": hit["_score"],
                "id": hit["_id"]
            } 
            for hit in response["hits"]["hits"]
        ]

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ошибка поиска: {str(e)}"
        )