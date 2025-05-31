from typing import List
from config.database import DatabaseManager
from apps.orders.schemas import OrderItemCreate, PaymentCreate
from apps.products.models import ProductVariant, Product
from apps.accounts.models import Seller
from fastapi import HTTPException, status
from apps.orders.models import Order, OrderItem, Payment
import uuid

class OrderService:
    @classmethod
    async def create_order(cls, user_id: int, items: List[OrderItemCreate]):
        with DatabaseManager.session as session:
            # Проверка наличия товаров
            for item in items:
                variant = session.get(ProductVariant, item.variant_id)
                if not variant:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Variant {item.variant_id} not found"
                    )
                product = session.get(Product, variant.product_id)
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product {variant.product_id} not found"
                    )
                seller = session.get(Seller, product.seller_id)
                if not seller:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Seller {product.seller_id} not found"
                    )
                if variant.stock < item.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Недостаточно товара {item.variant_id}"
                    )
            
            # Создание заказа
            order = Order(user_id=user_id, status="created", total_amount=0)
            session.add(order)
            session.flush()
            
            # Добавление товаров
            total = 0
            for item in items:
                variant = session.get(ProductVariant, item.variant_id)
                product = session.get(Product, variant.product_id)
                seller = session.get(Seller, product.seller_id)
                
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=variant.product_id,
                    variant_id=variant.id,
                    seller_id=seller.id,
                    quantity=item.quantity,
                    price=variant.price
                )
                total += variant.price * item.quantity
                variant.stock -= item.quantity  # Уменьшаем остаток
                session.add(order_item)
            
            order.total_amount = total
            session.commit()
            
            return {"order_id": order.id, "total": total}
    
    @staticmethod
    async def get_order_detail(order_id: int, user_id: int):
        with DatabaseManager.session as session:
            order = session.get(Order, order_id)
            if not order or order.user_id != user_id:
                raise HTTPException(status_code=404, detail="Order not found")
            
            items = []
            for item in order.items:
                product = session.get(Product, item.product_id)
                variant = session.get(ProductVariant, item.variant_id)
                
                items.append({
                    "product_name": product.product_name,
                    "variant_info": f"{variant.price} USD",  # Пример, можно добавить больше данных
                    "quantity": item.quantity,
                    "price": item.price,
                    "seller_id": item.seller_id  # Добавляем в ответ
                })
            
            return {
                "id": order.id,
                "status": order.status,
                "total_amount": order.total_amount,
                "created_at": order.created_at,
                "items": items
            }

class PaymentService:
    @staticmethod
    async def process_payment(order_id: int, user_id: int, payment_data: PaymentCreate):
        with DatabaseManager.session as session:
            order = session.get(Order, order_id)
            if not order or order.user_id != user_id:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Интеграция с платежной системой (заглушка)
            payment = Payment(
                order_id=order_id,
                amount=order.total_amount,
                method=payment_data.method,
                status="pending"
            )
            session.add(payment)
            
            # Здесь должна быть реальная интеграция с платежным шлюзом
            payment.status = "completed"
            payment.transaction_id = f"txn_{uuid.uuid4().hex}"
            order.status = "paid"
            
            session.commit()
            return {"status": "success", "transaction_id": payment.transaction_id}