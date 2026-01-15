from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Optional

class SensorStatusBreakdown(BaseModel):
    정상: int
    경고: int
    오류: int
    오프라인: int

class BottleneckIndicator(BaseModel):
    is_congested: bool
    bottleneck_score: float

class AggregatedSensorDataCreate(BaseModel):
    aggregated_id: str
    zone_id: str
    line_direction: str
    timestamp: str
    aggregation_interval_sec: int
    item_throughput: int
    avg_speed: float
    sensor_status_breakdown: Dict
    bottleneck_indicator: Dict

class AggregatedSensorDataResponse(BaseModel):
    id: int
    aggregated_id: str
    zone_id: str
    line_direction: str
    timestamp: str
    aggregation_interval_sec: int
    item_throughput: int
    avg_speed: float
    sensor_status_breakdown: Dict
    bottleneck_indicator: Dict
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
