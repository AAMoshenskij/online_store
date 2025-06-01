# apps/analytics/models.py
from sqlalchemy import Column, Integer, String, DateTime, func
from config.database import FastModel

class UserActivity(FastModel):
    __tablename__ = "user_activities" 
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)  # Null для анонимных
    product_id = Column(Integer)
    action = Column(String(50))  # 'view', 'purchase', 'review'
    timestamp = Column(DateTime, server_default=func.now())  # Исправлено на server_default
