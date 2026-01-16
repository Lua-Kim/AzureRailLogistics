from pydantic import BaseModel
from typing import List, Optional

class LogisticsZoneBase(BaseModel):
    zone_id: str
    name: str
    lines: int
    length: float
    sensors: int

class LogisticsZoneCreate(LogisticsZoneBase):
    pass

class LogisticsZone(LogisticsZoneBase):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class ZonesConfig(BaseModel):
    """전체 zones 설정"""
    zones: List[LogisticsZone]
