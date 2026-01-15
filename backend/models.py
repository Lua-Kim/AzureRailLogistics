from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from database import Base
import datetime

class AggregatedSensorData(Base):
    __tablename__ = "aggregated_sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    aggregated_id = Column(String, index=True)  # e.g., "IN-A01-S1"
    zone_id = Column(String, index=True)        # e.g., "IN-A01"
    line_direction = Column(String)             # e.g., "Inbound"
    timestamp = Column(String)                  # ISO format timestamp string
    aggregation_interval_sec = Column(Integer)  # e.g., 5
    item_throughput = Column(Integer)           # 통과한 아이템 수
    avg_speed = Column(Float)                   # 평균 속도
    sensor_status_breakdown = Column(JSON)      # {"정상": 10, "경고": 2, "오류": 0, "오프라인": 0}
    bottleneck_indicator = Column(JSON)         # {"is_congested": False, "bottleneck_score": 0.3}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    class Config:
        from_attributes = True
