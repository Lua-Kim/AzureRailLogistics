from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class LogisticsZoneBase(BaseModel):
    zone_id: str
    name: str
    lines: int
    length: float
    sensors: int

class LogisticsZoneCreate(LogisticsZoneBase):
    pass

class LogisticsLineBase(BaseModel):
    line_id: str
    sensors: int = 0

class LogisticsLineCreate(LogisticsLineBase):
    zone_id: str

class LogisticsLine(LogisticsLineBase):
    id: int
    zone_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class LogisticsZone(LogisticsZoneBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    zone_lines: List[LogisticsLine] = []
    
    class Config:
        from_attributes = True

class ZonesConfig(BaseModel):
    """전체 zones 설정"""
    zones: List[LogisticsZone]
