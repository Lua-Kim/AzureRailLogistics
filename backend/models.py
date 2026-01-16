from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class LogisticsZone(Base):
    """물류 구획 설정 모델"""
    __tablename__ = "logistics_zones"
    
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String, unique=True, index=True)  # e.g., "IB-01"
    name = Column(String)  # e.g., "입고"
    lines = Column(Integer)  # 라인 개수
    length = Column(Float)  # 라인 길이 (m)
    sensors = Column(Integer)  # 센서 개수
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    class Config:
        from_attributes = True
