from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, ARRAY, Numeric
from sqlalchemy.orm import relationship

from config.database import FastModel
from sqlalchemy.orm import Session


class Order(FastModel):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="created")  # created, paid, shipped, delivered, cancelled
    total_amount = Column(Numeric(10, 2))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    items = relationship("OrderItem", back_populates="order")
    user = relationship("User")

class OrderItem(FastModel):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    variant_id = Column(Integer, ForeignKey("product_variants.id"))
    seller_id = Column(Integer, ForeignKey("sellers.id"))
    quantity = Column(Integer)
    price = Column(Numeric(10, 2))
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    seller = relationship("Seller")

class Payment(FastModel):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    amount = Column(Numeric(10, 2))
    method = Column(String(20))  # card, PayPal, etc.
    status = Column(String(20))  # pending, completed, failed
    transaction_id = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())