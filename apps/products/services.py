from itertools import product as options_combination
from typing import Optional, List, Union

from fastapi import Request
from sqlalchemy import select, and_, or_

from apps.core.date_time import DateTime
from apps.core.services.media import MediaService
from apps.products.models import Product, ProductOption, ProductOptionItem, ProductVariant, ProductMedia
from config import settings
from config.database import DatabaseManager
from sqlalchemy.orm import Session
from apps.accounts.models import User


class ProductService:
    request: Optional[Request]= None
    product = None
    price: Union[int, float]
    stock: int
    options: Optional[List] = [] 
    options_data: List = []
    variants: List = []
    media: Optional[List] = None

    @classmethod
    def __init__(cls, request: Optional[Request] = None):
        cls.request = request

    @classmethod
    def create_product(cls, data: dict, get_obj: bool = False):

        cls._create_product(data)
        cls.__create_product_options()
        cls.__create_variants()

        if get_obj:
            return cls.product
        return cls.retrieve_product(cls.product.id)

    @classmethod
    def _create_product(cls, data: dict):
        cls.price = data.pop('price', 0)
        cls.stock = data.pop('stock', 0)
        cls.options_data = data.pop('options', [])
        cls.seller_id = data.pop('seller_id')

        if 'status' in data:
            # Check if the value is one of the specified values, if not, set it to 'draft'
            valid_statuses = ['active', 'archived', 'draft']
            if data['status'] not in valid_statuses:
                data['status'] = 'draft'

        # create a product
        with DatabaseManager.session as db:
            cls.product = Product.create(**data, seller_id=cls.seller_id)

            cls._update_seller_products(db)

    @classmethod
    def _update_seller_products(cls, db: Session):
        """Обновляем product_ids у продавца"""
        from apps.accounts.models import Seller
        
        seller = db.query(Seller).get(cls.seller_id)
        if seller:
            # Инициализируем product_ids если None
            if seller.product_ids is None:
                seller.product_ids = []
            
            # Добавляем новый product_id если его еще нет
            if cls.product.id not in seller.product_ids:
                seller.product_ids = list(seller.product_ids) + [cls.product.id]
                db.commit()

    @classmethod
    def __create_product_options(cls):
        """
        Create new option if it doesn't exist and update its items,
        and ensures that options are uniq in a product and also items in each option are uniq.
        """

        if cls.options_data:
            for option in cls.options_data:

                # Creates a new instance of the ProductOption model, adds it to the database,
                # and commits the transaction. Returns the newly created model instance
                new_option = ProductOption.create(product_id=cls.product.id, option_name=option['option_name'])

                for item in option['items']:
                    ProductOptionItem.create(option_id=new_option.id, item_name=item)
            cls.options = cls.retrieve_options(cls.product.id)
        else:
            cls.options = None

    @classmethod
    def retrieve_options(cls, product_id):
        """
        Get all options of a product
        """

        product_options = []
        options = ProductOption.filter(ProductOption.product_id == product_id).all()
        for option in options:
            # Retrieves records from the database based on a given filter condition.
            # Returns a list of model instances matching the filter condition.
            items = ProductOptionItem.filter(ProductOptionItem.option_id == option.id).all()

            product_options.append({
                'options_id': option.id,
                'option_name': option.option_name,
                'items': [{'item_id': item.id, 'item_name': item.item_name} for item in items]
            })
        if product_options:
            return product_options
        else:
            return None

    @classmethod
    def __create_variants(cls):
        """
        Create a default variant or create variants by options combination.
        """

        if cls.options:

            # create variants by options combination
            items_id = cls.get_item_ids_by_product_id(cls.product.id)
            variants = list(options_combination(*items_id))
            for variant in variants:
                values_tuple = tuple(variant)

                # set each value to an option and set none if it doesn't exist
                while len(values_tuple) < 3:
                    values_tuple += (None,)
                option1, option2, option3 = values_tuple

                ProductVariant.create(
                    product_id=cls.product.id,
                    option1=option1,
                    option2=option2,
                    option3=option3,
                    price=cls.price,
                    stock=cls.stock
                )
        else:
            # set a default variant
            ProductVariant.create(
                product_id=cls.product.id,
                price=cls.price,
                stock=cls.stock
            )

        cls.variants = cls.retrieve_variants(cls.product.id)

    @classmethod
    def retrieve_variants(cls, product_id):
        """
        Get all variants of a product
        """

        product_variants = []
        variants: list[ProductVariant] = ProductVariant.filter(ProductVariant.product_id == product_id).all()
        for variant in variants:
            product_variants.append(
                {
                    "variant_id": variant.id,
                    "product_id": variant.product_id,
                    "price": variant.price,
                    "stock": variant.stock,
                    "option1": variant.option1,
                    "option2": variant.option2,
                    "option3": variant.option3,
                    "created_at": DateTime.string(variant.created_at),
                    "updated_at": DateTime.string(variant.updated_at)
                })

        if product_variants:
            return product_variants
        return None

    @staticmethod
    def retrieve_variant(variant_id: int):
        variant = ProductVariant.get_or_404(variant_id)
        variant_data = {
            "variant_id": variant.id,
            "product_id": variant.product_id,
            "price": variant.price,
            "stock": variant.stock,
            "option1": variant.option1,
            "option2": variant.option2,
            "option3": variant.option3,
            "created_at": DateTime.string(variant.created_at),
            "updated_at": DateTime.string(variant.updated_at)
        }
        return variant_data

    @classmethod
    def get_item_ids_by_product_id(cls, product_id):
        item_ids_by_option = []
        item_ids_dict = {}
        with DatabaseManager.session as session:

            # Query the ProductOptionItem table to retrieve item_ids
            items = (
                session.query(ProductOptionItem.option_id, ProductOptionItem.id)
                .join(ProductOption)
                .filter(ProductOption.product_id == product_id)
                .all()
            )

            # Separate item_ids by option_id
            for option_id, item_id in items:
                if option_id not in item_ids_dict:
                    item_ids_dict[option_id] = []
                item_ids_dict[option_id].append(item_id)

            # Append `item_ids` lists to the result list
            item_ids_by_option.extend(item_ids_dict.values())

        return item_ids_by_option

    @classmethod
    def retrieve_product(cls, product_id):
        cls.product = Product.get_or_404(product_id)
        cls.options = cls.retrieve_options(product_id)
        cls.variants = cls.retrieve_variants(product_id)
        cls.media = cls.retrieve_media_list(product_id)

        product = {
            'product_id': cls.product.id,
            'product_name': cls.product.product_name,
            'description': cls.product.description,
            'status': cls.product.status,
            'created_at': DateTime.string(cls.product.created_at),
            'updated_at': DateTime.string(cls.product.updated_at),
            'published_at': DateTime.string(cls.product.published_at),
            'options': cls.options,
            'variants': cls.variants,
            'media': cls.media
        }
        return product

    @classmethod
    def update_product(cls, product_id, current_user, **kwargs):
        """Update product with seller permission check"""
        product = Product.get_or_404(product_id)
        
        # Проверяем, является ли пользователь продавцом и владельцем товара
        if current_user.role != 'admin':
            seller = Seller.filter(Seller.user_id == current_user.id).first()
            if not seller or product_id not in seller.product_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to update this product"
                )

        # Обновляем данные
        kwargs['updated_at'] = DateTime.now()
        Product.update(product_id, **kwargs)
        return cls.retrieve_product(product_id)

    @classmethod
    def update_variant(cls, variant_id: int, current_user: User, **kwargs):
        variant = ProductVariant.get_or_404(variant_id)
        product_id = variant.product_id
        
        if current_user.role == 'admin':
            pass  # Админ имеет полный доступ
        elif current_user.role == 'seller':
            seller = Seller.filter(Seller.user_id == current_user.id).first()
            
            if not seller:
                raise HTTPException(403, "Seller profile not found")
                
            # ВАЖНО: Проверяем ДО изменений
            if not seller.product_ids or product_id not in seller.product_ids:
                raise HTTPException(403, "You don't own this product")
        else:
            raise HTTPException(403, "Admin or seller rights required")

        # Обновляем вариант
        kwargs['updated_at'] = DateTime.now()
        ProductVariant.update(variant_id, **kwargs)
        return cls.retrieve_variant(variant_id)

    @classmethod
    def list_products(cls, limit: int = 12):
        # - if "default variant" is not set, first variant will be
        # - on list of products, for price, get it from "default variant"
        # - if price or stock of default variant is 0 then select first variant that is not 0
        # - or for price, get it from "less price"
        # do all of them with graphql and let the front devs decide witch query should be run.

        # also can override the list `limit` in settings.py
        if hasattr(settings, 'products_list_limit'):
            limit = settings.products_list_limit

        products_list = []

        with DatabaseManager.session as session:
            products = session.execute(
                select(Product.id).limit(limit)
            )

        for product in products:
            products_list.append(cls.retrieve_product(product.id))

        return products_list
        # --- list by join ----
        # products_list = []
        # with DatabaseManager.session as session:
        #     products = select(
        #         Product.id,
        #         Product.product_name,
        #         coalesce(ProductMedia.alt, None).label('alt'),
        #         coalesce(ProductMedia.src, None).label('src'),
        #         # media.alt,
        #         ProductVariant.price,
        #         ProductVariant.stock
        #     ).outerjoin(ProductMedia).outerjoin(ProductVariant)
        #     products = session.execute(products)
        #
        # for product in products:
        #     media = {'src': product.src, 'alt': product.alt} if product.src is not None else None
        #     products_list.append(
        #         {
        #             'product_id': product.id,
        #             'product_name': product.product_name,
        #             'price': product.price,
        #             'stock': product.stock,
        #             'media': media
        #         }
        #     )

    @classmethod
    def create_media(cls, product_id, alt, files):
        """
        Save uploaded media to `media` directory and attach uploads to a product.
        """

        product: Product = Product.get_or_404(product_id)
        media_service = MediaService(parent_directory="/products", sub_directory=product_id)

        for file in files:
            file_name, file_extension = media_service.save_file(file)
            ProductMedia.create(
                product_id=product_id,
                alt=alt if alt is not None else product.product_name,
                src=file_name,
                type=file_extension
            )

        media = cls.retrieve_media_list(product_id)
        return media

    @classmethod
    def retrieve_media_list(cls, product_id):
        """
        Get all media of a product.
        """

        media_list = []
        product_media: list[ProductMedia] = ProductMedia.filter(ProductMedia.product_id == product_id).all()
        for media in product_media:
            media_list.append(
                {
                    "media_id": media.id,
                    "product_id": media.product_id,
                    "alt": media.alt,
                    "src": cls.__get_media_url(media.product_id, media.src),
                    "type": media.type,
                    "created_at": DateTime.string(media.created_at),
                    "updated_at": DateTime.string(media.updated_at)
                })
        if media_list:
            return media_list
        else:
            return None

    @classmethod
    def retrieve_single_media(cls, media_id):
        """
        Get a media by id.
        """

        media_obj = ProductMedia.filter(ProductMedia.id == media_id).first()
        if media_obj:
            media = {
                "media_id": media_obj.id,
                "product_id": media_obj.product_id,
                "alt": media_obj.alt,
                "src": cls.__get_media_url(media_obj.product_id, media_obj.src),
                "type": media_obj.type,
                "created_at": DateTime.string(media_obj.created_at),
                "updated_at": DateTime.string(media_obj.updated_at)
            }
            return media
        else:
            return None

    @classmethod
    def __get_media_url(cls, product_id, file_name: str):
        if cls.request is None:
            base_url = "http://127.0.0.1:8000/"
        else:
            base_url = str(cls.request.base_url)

        return f"{base_url}media/products/{product_id}/{file_name}" if file_name is not None else None

    @classmethod
    def update_media(cls, media_id, **kwargs):
        # check media exist
        media: ProductMedia = ProductMedia.get_or_404(media_id)
        file = kwargs.pop('file', None)
        if file is not None:
            media_service = MediaService(parent_directory="/products", sub_directory=media.product_id)
            file_name, file_extension = media_service.save_file(file)
            kwargs['src'] = file_name
            kwargs['type'] = file_extension

        # TODO `updated_at` is autoupdate dont need to code
        kwargs['updated_at'] = DateTime.now()
        ProductMedia.update(media_id, **kwargs)

        return cls.retrieve_single_media(media_id)

    @staticmethod
    def delete_product_media(product_id, media_ids: List[int]):

        # Fetch the product media records to be deleted
        with DatabaseManager.session as session:
            filters = [
                and_(ProductMedia.product_id == product_id, ProductMedia.id == media_id)
                for media_id in media_ids
            ]
            media_to_delete = session.query(ProductMedia).filter(or_(*filters)).all()

            # Delete the product media records
            for media in media_to_delete:
                ProductMedia.delete(ProductMedia.get_or_404(media.id))
        return None

    @classmethod
    def delete_product(cls, product_id: int, current_user: User):
        """Delete product with seller permission check"""
        product = Product.get_or_404(product_id)
        
        # Админы могут всё
        if current_user.role == 'admin':
            pass
        # Проверяем права продавца
        elif current_user.role == 'seller':
            seller = Seller.filter(Seller.user_id == current_user.id).first()
            if not seller:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Seller profile not found"
                )
            
            # Проверяем права ДО любых изменений
            if not seller.product_ids or product_id not in seller.product_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't own this product"
                )
            
            # Если права подтверждены - удаляем из списка продавца
            seller.product_ids = [pid for pid in seller.product_ids if pid != product_id]
            Seller.update(seller.id, product_ids=seller.product_ids)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or seller rights required"
            )

        # Удаляем сам продукт (если проверки прав пройдены)
        Product.delete(product)

    @classmethod
    def delete_media_file(cls, media_id: int):
        media = ProductMedia.get_or_404(media_id)
        product_id = media.product_id

        media_service = MediaService(parent_directory="/products", sub_directory=product_id)
        is_fie_deleted = media_service.delete_file(media.src)
        if is_fie_deleted:
            ProductMedia.delete(ProductMedia.get_or_404(media_id))
            return True
        return False


# Добавляем в apps/products/services.py

from sqlalchemy import or_, and_, func
from fastapi import HTTPException, status

@classmethod
def list_products(cls, page: int = 1, limit: int = 12, filters: dict = None):
    """
    Retrieve paginated and filtered list of products.
    """
    offset = (page - 1) * limit
    query = cls._build_product_query(filters)
    
    with DatabaseManager.session as session:
        # Get total count for pagination
        total = session.query(func.count(Product.id)).select_from(Product)
        if query is not None:
            total = total.filter(query)
        total = total.scalar()
        
        # Get paginated results
        products_query = session.query(Product)
        if query is not None:
            products_query = products_query.filter(query)
            
        products = products_query.offset(offset).limit(limit).all()
        
        products_list = []
        for product in products:
            products_list.append(cls.retrieve_product(product.id))
        
        return {
            "items": products_list,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit  # Calculate total pages
        }

@classmethod
def _build_product_query(cls, filters: dict):
    """
    Build SQLAlchemy query based on filters.
    """
    if not filters:
        return None
        
    conditions = []
    
    # Status filter
    if filters.get("status"):
        status_values = filters["status"].split(",")
        conditions.append(Product.status.in_(status_values))
    
    # Price range filter
    if filters.get("min_price") is not None or filters.get("max_price") is not None:
        # Join with variants to filter by price
        from apps.products.models import ProductVariant
        subquery = (
            DatabaseManager.session.query(ProductVariant.product_id)
            .group_by(ProductVariant.product_id)
            .having(func.min(ProductVariant.price) >= (filters.get("min_price") or 0))
            .having(func.max(ProductVariant.price) <= (filters.get("max_price") or float('inf')))
            .subquery()
        )
        conditions.append(Product.id.in_(subquery))
    
    # Search filter
    if filters.get("search"):
        search = f"%{filters['search']}%"
        conditions.append(
            or_(
                Product.product_name.ilike(search),
                Product.description.ilike(search)
            )
        )
    
    return and_(*conditions) if conditions else None

@classmethod
def get_products_paginated(cls, request: Request, page: int, per_page: int, filters: dict):
    """
    Get paginated list of products with optional filters
    
    Args:
        page: Page number (1-based)
        per_page: Items per page
        filters: Dictionary of filter parameters
        
    Returns:
        Dictionary with paginated products and metadata
    """
    query = select(Product).where(Product.status == 'active')
    
    # Apply filters
    if filters.get('status'):
        query = query.where(Product.status == filters['status'])
        
    if filters.get('min_price') is not None:
        query = query.join(ProductVariant).where(ProductVariant.price >= filters['min_price'])
        
    if filters.get('max_price') is not None:
        query = query.join(ProductVariant).where(ProductVariant.price <= filters['max_price'])
        
    if filters.get('seller_id'):
        query = query.where(Product.seller_id == filters['seller_id'])
        
    if filters.get('search'):
        search = f"%{filters['search']}%"
        query = query.where(Product.product_name.ilike(search))
    
    # Count total items
    total_query = select(func.count()).select_from(query)
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    with DatabaseManager.session as session:
        total = session.execute(total_query).scalar()
        products = session.execute(query).scalars().all()
        
        # Convert products to dict format
        product_list = [cls._product_to_dict(p) for p in products]
        
        return {
            "items": product_list,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

@classmethod
def _product_to_dict(cls, product: Product):
    """
    Convert Product object to dictionary with essential fields
    """
    variants = ProductVariant.filter(ProductVariant.product_id == product.id).all()
    main_variant = variants[0] if variants else None
    
    return {
        "id": product.id,
        "product_name": product.product_name,
        "description": product.description,
        "status": product.status,
        "price": main_variant.price if main_variant else 0,
        "image_url": cls._get_main_image_url(product.id, request),
        "seller_id": product.seller_id,
        "created_at": DateTime.string(product.created_at)
    }

@classmethod
def _get_main_image_url(cls, product_id: int, request: Request):
    """
    Get URL of the main product image
    """
    media = ProductMedia.filter(
        ProductMedia.product_id == product_id
    ).order_by(ProductMedia.id).first()
    
    if media:
        return str(request.base_url) + f"media/products/{product_id}/{media.src}"
    return None

from apps.accounts.models import Seller

@classmethod
def update_product(cls, product_id, current_user, **kwargs):
    """Update product with seller permission check"""
    product = Product.get_or_404(product_id)
    
    # Проверяем, является ли пользователь продавцом и владельцем товара
    if current_user.role != 'admin':
        seller = Seller.filter(Seller.user_id == current_user.id).first()
        if not seller or product_id not in seller.product_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this product"
            )

    # Обновляем данные
    kwargs['updated_at'] = DateTime.now()
    Product.update(product_id, **kwargs)
    return cls.retrieve_product(product_id)