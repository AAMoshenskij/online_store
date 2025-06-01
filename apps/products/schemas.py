from typing import List
from typing import Optional


from fastapi import Query, UploadFile
from pydantic import BaseModel, constr, field_validator, model_validator

"""
---------------------------------------
--------------- Variant ---------------
---------------------------------------
"""


class VariantSchema(BaseModel):
    variant_id: int
    product_id: int
    price: Optional[float]
    stock: int
    option1: Optional[int]
    option2: Optional[int]
    option3: Optional[int]
    created_at: str
    updated_at: Optional[str]


class UpdateVariantIn(BaseModel):
    price: Optional[float] = None
    stock: Optional[int] = None


class UpdateVariantOut(BaseModel):
    variant: VariantSchema


class RetrieveVariantOut(BaseModel):
    variant: VariantSchema


class ListVariantsOut(BaseModel):
    variants: List[VariantSchema]


"""
---------------------------------------
--------------- Options ---------------
---------------------------------------
"""


class OptionItemOut(BaseModel):
    item_id: int
    item_name: str


class OptionOut(BaseModel):
    options_id: int
    option_name: str
    items: List[OptionItemOut]


class OptionIn(BaseModel):
    option_name: constr(min_length=1)
    items: List[str]

    @field_validator('items')
    def not_empty(cls, value):
        if value is None or value == []:
            raise ValueError('items must not be None or empty')
        return value


"""
---------------------------------------
---------------- Media ----------------
---------------------------------------
"""


class ProductMediaSchema(BaseModel):
    media_id: int
    product_id: int
    alt: str
    src: str
    type: str
    updated_at: Optional[str]
    created_at: str


class CreateProductMediaOut(BaseModel):
    media: List[ProductMediaSchema]


class CreateProductMediaIn(BaseModel):
    product_id: int
    alt: str


class FileUpload(BaseModel):
    x_file: UploadFile


class MultiFileUpload(BaseModel):
    files: List[FileUpload]
    data: CreateProductMediaIn

    class Config:
        from_attributes = True


class RetrieveProductMediaOut(BaseModel):
    media: Optional[List[ProductMediaSchema]] = None 


class UpdateMediaOut(BaseModel):
    media: ProductMediaSchema


class RetrieveMediaOut(BaseModel):
    media: ProductMediaSchema


"""
---------------------------------------
--------------- Product ---------------
---------------------------------------
"""


class ProductSchema(BaseModel):
    product_id: int
    product_name: str = Query(..., max_length=255)
    description: Optional[str]
    status: Optional[str]

    created_at: str
    updated_at: Optional[str]
    published_at: Optional[str]

    options: Optional[List[OptionOut]] = None
    variants: Optional[List[VariantSchema]] = None
    media: Optional[List[ProductMediaSchema]] = None


class CreateProductOut(BaseModel):
    product: ProductSchema

    class Config:
        from_attributes = True


class CreateProductIn(BaseModel):
    product_name: str = Query(..., max_length=255, min_length=1)
    description: Optional[str] = None
    status: Optional[str] = None
    price: float = 0
    stock: int = 0
    #seller_id: int

    options: Optional[List[OptionIn]] = None

    class Config:
        from_attributes = True

    @field_validator('price')
    def validate_price(cls, price):
        if price < 0:
            raise ValueError('Price must be a positive number.')
        return price

    @field_validator('stock')
    def validate_stock(cls, stock):
        if stock < 0:
            raise ValueError('Stock must be a positive number.')
        return stock

    @model_validator(mode='before')
    def validate_uniqueness(cls, values):
        options = values.get("options", [])
        option_name_set = set()
        items_set = set()

        # each product should have just max 3 options.
        if len(options) > 3:
            raise ValueError('The number of options cannot exceed 3.')

        # checking `options-name` and `option-items list` are uniq
        for option in options:
            if isinstance(option, dict):
                option_name = option.get("option_name")
                items = option.get("items", [])
                if isinstance(option_name, str):
                    if option_name in option_name_set:
                        raise ValueError(f'Duplicate option name found: {option_name}')
                    option_name_set.add(option_name)
                    for item in items:
                        if isinstance(item, str):
                            if item in items_set:
                                raise ValueError(f'Duplicate item found in option "{option_name}": {item}')
                            items_set.add(item)
        return values


class RetrieveProductOut(BaseModel):
    product: ProductSchema


class ListProductIn(BaseModel):
    ...


class ListProductOut(BaseModel):
    products: List[ProductSchema]


class UpdateProductIn(BaseModel):
    product_name: Optional[str] = Query(None, max_length=255, min_length=1)
    description: Optional[str] = None
    status: Optional[str] = None


class UpdateProductOut(BaseModel):
    product: ProductSchema


# Добавляем в apps/products/schemas.py

class PaginatedProductList(BaseModel):
    items: List[ProductSchema]
    total: int
    page: int
    limit: int
    pages: int

class ListProductOut(BaseModel):
    products: PaginatedProductList