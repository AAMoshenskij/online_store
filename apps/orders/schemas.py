from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class OrderItemCreate(BaseModel):
    variant_id: int
    quantity: int = Field(gt=0, le=100)

class OrderDetail(BaseModel):
    id: int
    status: str
    total_amount: float
    created_at: datetime
    items: List["OrderItemDetail"]  # Строковая аннотация

class OrderItemDetail(BaseModel):
    product_name: str
    variant_info: str
    quantity: int
    price: float
    seller_id: int

class PaymentCreate(BaseModel):
    method: str = Field(..., pattern="^(card|paypal)$")
    card_token: Optional[str]

# Обновляем forward references
OrderDetail.model_rebuild()