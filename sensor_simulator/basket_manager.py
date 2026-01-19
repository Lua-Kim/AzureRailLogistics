import random
from typing import Dict, Optional, List
from datetime import datetime


class BasketPool:
    """바스켓 풀 관리 클래스"""
    
    def __init__(self, pool_size: int = 100):
        """
        Args:
            pool_size: 바스켓 풀 크기
        """
        self.pool_size = pool_size
        self.baskets: Dict[str, dict] = {}
        self._initialize_pool()
    
    def _initialize_pool(self):
        """바스켓 풀 초기화"""
        for i in range(1, self.pool_size + 1):
            basket_id = f"BASKET-{i:05d}"
            self.baskets[basket_id] = {
                "basket_id": basket_id,
                "zone_id": None,
                "line_id": None,
                "destination": None,
                "status": "available",  # available, in_transit, arrived
                "assigned_at": None,
                "updated_at": None
            }
    
    def get_basket(self, basket_id: str) -> Optional[dict]:
        """특정 바스켓 조회"""
        return self.baskets.get(basket_id)
    
    def get_random_basket(self) -> dict:
        """랜덤 바스켓 선택"""
        basket_id = random.choice(list(self.baskets.keys()))
        return self.baskets[basket_id]
    
    def get_all_baskets(self) -> Dict[str, dict]:
        """전체 바스켓 조회"""
        return self.baskets
    
    def assign_basket(self, basket_id: str, zone_id: str, line_id: str, destination: str) -> Optional[dict]:
        """바스켓에 존, 라인, 목적지 할당"""
        basket = self.baskets.get(basket_id)
        if not basket:
            return None
        
        basket["zone_id"] = zone_id
        basket["line_id"] = line_id
        basket["destination"] = destination
        basket["status"] = "in_transit"
        basket["assigned_at"] = datetime.now().isoformat()
        basket["updated_at"] = datetime.now().isoformat()
        
        return basket
    
    def update_basket_status(self, basket_id: str, status: str, zone_id: str = None, line_id: str = None) -> Optional[dict]:
        """바스켓 상태 및 위치 업데이트"""
        basket = self.baskets.get(basket_id)
        if not basket:
            return None
        
        basket["status"] = status
        if zone_id:
            basket["zone_id"] = zone_id
        if line_id:
            basket["line_id"] = line_id
        basket["updated_at"] = datetime.now().isoformat()
        
        return basket
    
    def get_available_baskets(self) -> List[dict]:
        """사용 가능한 바스켓 목록 조회"""
        return [b for b in self.baskets.values() if b["status"] == "available"]
    
    def get_baskets_by_status(self, status: str) -> List[dict]:
        """상태별 바스켓 조회"""
        return [b for b in self.baskets.values() if b["status"] == status]
    
    def get_baskets_by_zone(self, zone_id: str) -> List[dict]:
        """존별 바스켓 조회"""
        return [b for b in self.baskets.values() if b["zone_id"] == zone_id]
    
    def reset_basket(self, basket_id: str) -> Optional[dict]:
        """바스켓 초기화 (다시 사용 가능 상태로)"""
        basket = self.baskets.get(basket_id)
        if not basket:
            return None
        
        basket["zone_id"] = None
        basket["line_id"] = None
        basket["destination"] = None
        basket["status"] = "available"
        basket["updated_at"] = datetime.now().isoformat()
        
        return basket
    
    def get_statistics(self) -> dict:
        """바스켓 풀 통계 정보"""
        stats = {
            "total": len(self.baskets),
            "available": 0,
            "in_transit": 0,
            "arrived": 0,
            "by_zone": {},
            "by_zone_line": []
        }
        
        zone_line_map = {}
        
        for basket in self.baskets.values():
            status = basket["status"]
            if status in stats:
                stats[status] += 1
            
            zone_id = basket.get("zone_id")
            line_id = basket.get("line_id")
            
            if zone_id:
                if zone_id not in stats["by_zone"]:
                    stats["by_zone"][zone_id] = 0
                stats["by_zone"][zone_id] += 1
                
                if line_id:
                    key = f"{zone_id}|{line_id}"
                    if key not in zone_line_map:
                        zone_line_map[key] = {"zone_id": zone_id, "line_id": line_id, "count": 0}
                    zone_line_map[key]["count"] += 1
        
        stats["by_zone_line"] = list(zone_line_map.values())
        
        return stats
