"""
**Product Definition: Variable Products**

In our system, every product is considered a variable product.
Variable products encapsulate all product variations, streamlining the entire process.
Whether you create a product without any specified options or define up to three distinct options, each with a
single item, you are essentially working with a variable product.


**Product Variants and Options**

- **Variants:**
Products can have multiple variants, each representing a unique combination of attributes like price, stock, and other
 specifications.

- **Options:**
Products may feature up to three distinct options. Each option can have multiple items, allowing fora rich variety of
 choices.


**Simplified Product Management:**

All operations related to products, such as managing shopping carts, processing orders, and handling stock,
 are performed through product variants. This streamlined approach enhances efficiency and simplifies product
 handling across the platform.

Every time we create product, the media should be None, because the Media after creating a product will be
attached to it.
"""

from fastapi import APIRouter, status, Form, UploadFile, File, HTTPException, Query, Path, Depends
from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, List, Union

from apps.accounts.services.permissions import Permission
from apps.core.services.media import MediaService
from apps.products import schemas
from apps.products.services import ProductService
from apps.accounts.models import User
from fastapi import FastAPI, HTTPException, status
import logging
from prometheus_client import Summary
from apps.core.metrics import PRODUCTS_VIEWED_TOTAL

router = APIRouter(
    #dependencies=[Depends(Permission.is_authenticated)],  # Все endpoints требуют auth
    prefix="/products",
    #tags=["Products"]
)


# -----------------------
# --- Product Routers ---
# -----------------------


# apps/products/routers.py
@router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.CreateProductOut,
    summary='Create a new product',
    description='Create a new product.',
    tags=["Product"])
async def create_product(
    request: Request,
    product: schemas.CreateProductIn,
    current_user: User = Depends(Permission.is_seller)  # Только продавцы могут создавать товары
):
    # Добавляем seller_id из текущего пользователя
    product_data = product.model_dump()
    product_data['seller_id'] = current_user.seller_profile[0].id
    
    return {'product': ProductService(request).create_product(product_data)}


@router.get(
    '/{product_id}',
    status_code=status.HTTP_200_OK,
    response_model=schemas.RetrieveProductOut,
    summary='Retrieve a single product',
    description="Retrieve a single product.",
    tags=["Product"])
async def retrieve_product(request: Request, product_id: int):
    product_data = ProductService(request).retrieve_product(product_id)
    if product_data:
        PRODUCTS_VIEWED_TOTAL.labels(product_id=str(product_id), category_id="unknown").inc()
    return {"product": product_data}


@router.get(
    '/',
    status_code=status.HTTP_200_OK,
    response_model=schemas.ListProductOut,
    summary='Retrieve a list of products',
    description='Retrieve a list of products.',
    tags=["Product"])
async def list_produces(request: Request):
    products = ProductService(request).list_products()
    if products:
        return {'products': products}
    return JSONResponse(
        content=None,
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.put(
    '/variants/{variant_id}',
    status_code=status.HTTP_200_OK,
    response_model=schemas.UpdateVariantOut,
    summary='Updates an existing product variant',
    description='Modify an existing Product Variant.',
    tags=['Product Variant'])
async def update_variant(
    variant_id: int,
    payload: schemas.UpdateVariantIn,
    current_user: User = Depends(Permission.is_seller)
):
    update_data = {}
    for key, value in payload.model_dump().items():
        if value is not None:
            update_data[key] = value
    
    try:
        updated_variant = ProductService.update_variant(
            variant_id=variant_id,
            current_user=current_user,
            **update_data
        )
        return {'variant': updated_variant}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product variant"
        )


@router.delete(
    '/{product_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Deletes an existing product',
    description='Deletes an existing product.',
    tags=['Product'],
    dependencies=[Depends(Permission.is_admin)])
async def delete_product(
    product_id: int,
    current_user: User = Depends(Permission.is_seller)
):
    try:
        ProductService.delete_product(product_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )



# -------------------------------
# --- Product-Variant Routers ---
# -------------------------------


@router.put(
    '/variants/{variant_id}',
    status_code=status.HTTP_200_OK,
    response_model=schemas.UpdateVariantOut,
    summary='Updates an existing product variant',
    description='Modify an existing Product Variant.',
    tags=['Product Variant'],
    dependencies=[Depends(Permission.is_admin)])
async def update_variant(variant_id: int, payload: schemas.UpdateVariantIn):
    update_data = {}

    for key, value in payload.model_dump().items():
        if value is not None:
            update_data[key] = value
    try:
        updated_variant = ProductService.update_variant(variant_id, **update_data)
        return {'variant': updated_variant}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    '/variants/{variant_id}',
    status_code=status.HTTP_200_OK,
    response_model=schemas.RetrieveVariantOut,
    summary='Retrieve a single product variant',
    description='Retrieves a single product variant.',
    tags=['Product Variant'])
async def retrieve_variant(variant_id: int):
    return {'variant': ProductService.retrieve_variant(variant_id)}


@router.get(
    '/{product_id}/variants',
    status_code=status.HTTP_200_OK,
    response_model=schemas.ListVariantsOut,
    summary='Retrieves a list of product variants',
    description='Retrieves a list of product variants.',
    tags=['Product Variant'])
async def list_variants(product_id: int):
    return {'variants': ProductService.retrieve_variants(product_id)}


# -----------------------------
# --- Product-Media Routers ---
# -----------------------------
"""
when updating a product, actions on product's images are:
- add new images to product: mean attach new images to an existing product, this is the same as `create_product_media()`
- delete some images for product: mean unattached images from a product
"""


@router.post(
    '/{product_id}/media',
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.CreateProductMediaOut,
    summary="Create a new product image",
    description="Create a new product image.",
    tags=['Product Image'],
    dependencies=[Depends(Permission.is_admin)])
async def create_product_media(request: Request, x_files: List[UploadFile] = File(), product_id: int = Path(),
                               alt: Optional[str] = Form(None)):
    # check the file size and type
    for file in x_files:
        MediaService.is_allowed_extension(file)
        await MediaService.is_allowed_file_size(file)

    media = ProductService(request).create_media(product_id=product_id, alt=alt, files=x_files)
    return {'media': media}


@router.get(
    '/media/{media_id}',
    status_code=status.HTTP_200_OK,
    response_model=schemas.RetrieveMediaOut,
    summary='Retrieve a single product image',
    description='Get a single product image by id.',
    tags=['Product Image'])
async def retrieve_single_media(request: Request, media_id: int):
    return {'media': ProductService(request).retrieve_single_media(media_id)}


@router.get(
    '/{product_id}/media',
    status_code=status.HTTP_200_OK,
    response_model=schemas.RetrieveProductMediaOut,
    summary="Receive a list of all Product Images",
    description="Receive a list of all Product Images.",
    tags=['Product Image'])
async def list_product_media(request: Request, product_id: int):
    media = ProductService(request).retrieve_media_list(product_id=product_id)
    if media:
        return {'media': media}
    return JSONResponse(
        content=None,
        status_code=status.HTTP_204_NO_CONTENT
    )


@router.put(
    '/media/{media_id}',
    status_code=status.HTTP_200_OK,
    response_model=schemas.UpdateMediaOut,
    summary='Updates an existing image',
    description='Updates an existing image.',
    tags=['Product Image'],
    dependencies=[Depends(Permission.is_admin)])
async def update_media(request: Request, media_id: int, file: UploadFile = File(), alt: Optional[str] = Form(None)):
    update_data = {}

    if file is not None:
        update_data['file'] = file

    if alt is not None:
        update_data['alt'] = alt

    try:
        updated_media = ProductService(request).update_media(media_id, **update_data)
        return {'media': updated_media}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete(
    '/{product_id}/media',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete image from a product',
    description='Delete image from a product.',
    tags=['Product Image'],
    dependencies=[Depends(Permission.is_admin)])
async def delete_product_media(product_id: int, media_ids: str = Query(...)):
    media_ids_list = list(map(int, media_ids.split(',')))
    ProductService.delete_product_media(product_id, media_ids_list)


@router.delete(
    '/media/{media_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Delete a media file',
    description='Delete a media file.',
    tags=['Product Image'],
    dependencies=[Depends(Permission.is_admin)])
async def delete_media_file(media_id: int):
    ProductService.delete_media_file(media_id)


from fastapi import Query

@router.get(
    '/',
    status_code=status.HTTP_200_OK,
    response_model=schemas.ListProductOut,
    summary='Retrieve a list of products',
    description="""Retrieve a list of products with pagination and filtering.
    
    **Filters**:
    - status: Filter by product status (active, archived, draft)
    - min_price: Minimum product price
    - max_price: Maximum product price
    - search: Search in product names and descriptions
    
    **Pagination**:
    - page: Page number (default 1)
    - limit: Items per page (default 12)
    """,
    tags=['Product'])
async def list_produces(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status (active, archived, draft)"),
    min_price: Optional[float] = Query(None, description="Minimum product price"),
    max_price: Optional[float] = Query(None, description="Maximum product price"),
    search: Optional[str] = Query(None, description="Search in product names and descriptions"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(12, ge=1, le=100, description="Items per page")
):
    filters = {
        "status": status,
        "min_price": min_price,
        "max_price": max_price,
        "search": search
    }
    
    products = ProductService(request).list_products(page=page, limit=limit, filters=filters)
    if products:
        return {'products': products}
    return JSONResponse(
        content=None,
        status_code=status.HTTP_204_NO_CONTENT
    )