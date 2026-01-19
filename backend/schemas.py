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
class BasketBase(BaseModel):
    basket_id: str
    zone_id: Optional[str] = None
    line_id: Optional[str] = None
    width_cm: float
    destination: Optional[str] = None
    status: str  # available, in_transit, arrived
    assigned_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BasketCreate(BasketBase):
    pass

class BasketUpdate(BaseModel):
    zone_id: Optional[str] = None
    line_id: Optional[str] = None
    destination: Optional[str] = None
    status: Optional[str] = None

class Basket(BasketBase):
    line_length: Optional[float] = None  # DB에서 추가되는 필드
    
    class Config:
        from_attributes = True

class BasketsResponse(BaseModel):
    """바스켓 조회 응답"""
    count: int
    baskets: List[Basket]
    statistics: dict

class BasketCreateRequest(BaseModel):
    """바스켓 생성 요청"""
    zone_id: str              # IB-01
    line_id: str              # IB-01-001
    count: int                # 생성할 바스켓 수
    destination: Optional[str] = None  # 목적지 (선택사항)

class BasketCreateResponse(BaseModel):
    """바스켓 생성 응답"""
    success: bool
    created_count: int
    baskets: List[Basket]
    message: str