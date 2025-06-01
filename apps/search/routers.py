from fastapi import APIRouter, Query, HTTPException
from .services import search_products
from typing import List, Dict
from config.elasticsearch import es

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/", response_model=List[Dict])
async def search(
    q: str = Query(..., min_length=2, description="Search query"),
    category: str = Query(None, description="Filter by category"),
    min_rating: float = Query(None, ge=0, le=5, description="Minimum rating filter")
):
    try:
        return await search_products(q, category, min_rating)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    
