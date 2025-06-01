from typing import List
from config.database import DatabaseManager
from apps.orders.schemas import OrderItemCreate, PaymentCreate
from apps.products.models import ProductVariant, Product
from apps.accounts.models import Seller
from fastapi import HTTPException, status
from apps.orders.models import Order, OrderItem, Payment
import uuid

try:
    from ...core.metrics import (
        ORDERS_CREATED_TOTAL,
        ORDERS_AMOUNT_HISTOGRAM,
        ORDERS_STATUS_CHANGED_TOTAL,
        PAYMENTS_PROCESSED_TOTAL,
        ORDERS_COMPLETED_TOTAL
    )
except ImportError:
    from apps.core.metrics import (
        ORDERS_CREATED_TOTAL,
        ORDERS_AMOUNT_HISTOGRAM,
        ORDERS_STATUS_CHANGED_TOTAL,
        PAYMENTS_PROCESSED_TOTAL,
        ORDERS_COMPLETED_TOTAL
    )

class OrderService:
    @classmethod
    async def create_order(cls, user_id: int, items: List[OrderItemCreate]):
        with DatabaseManager.session as session:
            for item in items:
                variant = session.get(ProductVariant, item.variant_id)
                product = session.get(Product, variant.product_id)
                seller = session.get(Seller, product.seller_id)
                if not variant or variant.stock < item.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Недостаточно товара {item.variant_id}"
                    )
            
            old_status = None
            new_status = "created"
            order = Order(user_id=user_id, status=new_status)
            session.add(order)
            session.flush()
            
            total = 0
            for item in items:
                variant = session.get(ProductVariant, item.variant_id)
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=variant.product_id,
                    variant_id=variant.id,
                    seller_id = seller.id,
                    quantity=item.quantity,
                    price=variant.price
                )
                total += variant.price * item.quantity
                variant.stock -= item.quantity
                session.add(order_item)
            
            order.total_amount = total
            session.commit()
            
            ORDERS_CREATED_TOTAL.inc()
            ORDERS_AMOUNT_HISTOGRAM.observe(total)
            ORDERS_STATUS_CHANGED_TOTAL.labels(old_status=str(old_status), new_status=new_status).inc()
            
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
                    "variant_info": f"{variant.price} USD", 
                    "quantity": item.quantity,
                    "price": item.price,
                    "seller_id": item.seller_id
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
            
            if order.status == "paid" or order.status == "completed":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order already paid")

            old_order_status = order.status
            payment_status_metric = "success"
            
            payment = Payment(
                order_id=order_id,
                amount=order.total_amount,
                method=payment_data.method,
                status="pending"
            )
            session.add(payment)
            session.flush()
            
            try:
                # Имитируем успех
                payment.status = "completed"
                payment.transaction_id = f"txn_{uuid.uuid4().hex}"
                order.status = "paid"
                
                session.commit()

                PAYMENTS_PROCESSED_TOTAL.labels(status=payment_status_metric, payment_method=payment_data.method).inc()
                ORDERS_STATUS_CHANGED_TOTAL.labels(old_status=old_order_status, new_status=order.status).inc()
                
                if order.status == "paid": 
                    ORDERS_COMPLETED_TOTAL.inc()

                return {"status": "success", "transaction_id": payment.transaction_id}
            except Exception as e:
                session.rollback()
                payment_status_metric = "failure_processing"
                PAYMENTS_PROCESSED_TOTAL.labels(status=payment_status_metric, payment_method=payment_data.method).inc()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Payment processing failed")