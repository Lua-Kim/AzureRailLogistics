from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
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
    
    # 관계 설정
    zone_lines = relationship("LogisticsLine", back_populates="zone", cascade="all, delete-orphan")
    
    class Config:
        from_attributes = True


class LogisticsLine(Base):
    """물류 라인 설정 모델"""
    __tablename__ = "logistics_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String, ForeignKey("logistics_zones.zone_id"), index=True)
    line_id = Column(String)  # e.g., "A", "B", "C", "D"
    length = Column(Float, default=0)  # 라인 길이 (m)
    sensors = Column(Integer, default=0)  # 라인별 센서 개수
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    zone = relationship("LogisticsZone", back_populates="zone_lines")
    
    class Config:
        from_attributes = True


class SensorEvent(Base):
    """센서 이벤트 데이터 (시계열)"""
    __tablename__ = "sensor_events"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, index=True, nullable=False)  # 이벤트 발생 시간
    zone_id = Column(String, index=True, nullable=False)      # 구획 ID
    basket_id = Column(String, index=True, nullable=True)     # 바스켓 ID
    sensor_id = Column(String, nullable=False)                # 센서 ID
    signal = Column(Boolean, default=False)                   # 신호 감지 여부
    speed = Column(Float, default=0.0)                        # 속도 (%)
    position_x = Column(Float, nullable=True)                 # X 좌표 (m)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    class Config:
        from_attributes = True
