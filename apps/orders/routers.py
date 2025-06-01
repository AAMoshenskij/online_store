from fastapi import APIRouter, status, Depends

from apps.orders import schemas
from apps.accounts.services.permissions import Permission
from apps.accounts.services.user import User
#from apps.orders.models import 
from typing import List
from apps.orders.services.order_service import OrderService, PaymentService


router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(
    items: List[schemas.OrderItemCreate],
    current_user: User = Depends(Permission.is_authenticated)
):
    """Создание нового заказа"""
    return await OrderService.create_order(current_user.id, items)

@router.post("/{order_id}/pay")
async def pay_order(
    order_id: int,
    payment_data: schemas.PaymentCreate,
    current_user: User = Depends(Permission.is_authenticated)
):
    """Оплата заказа"""
    return await PaymentService.process_payment(order_id, current_user.id, payment_data)

@router.get("/{order_id}", response_model=schemas.OrderDetail)
async def get_order(
    order_id: int,
    current_user: User = Depends(Permission.is_authenticated)
):
    """Получение информации о заказе"""
    return await OrderService.get_order_detail(order_id, current_user.id)