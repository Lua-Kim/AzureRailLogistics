import random
from typing import Dict, Optional, List
from datetime import datetime

# 바스켓 설정
BASKET_WIDTH_CM = 50  # 바스켓 폭 (cm)


class BasketPool:
    """바스켓 풀 관리 클래스"""
    
    def __init__(self, pool_size: int = 100, zones_lines_config: Optional[List[dict]] = None):
        """
        Args:
            pool_size: 바스켓 풀 크기
            zones_lines_config: 존-라인 설정 (라인별로 바스켓을 배분하고 싶을 때)
                예: [
                    {'zone_id': 'Z1', 'lines': [
                        {'line_id': 'A', 'length': 1000},
                        {'line_id': 'B', 'length': 1500}
                    ]},
                    ...
                ]
        """
        self.pool_size = pool_size
        self.zones_lines_config = zones_lines_config or []
        self.baskets: Dict[str, dict] = {}
        self._initialize_pool()
    
    def _initialize_pool(self):
        """바스켓 풀 초기화 - 존과 라인별로 랜덤 개수 배분 (라인 길이 제약 준수)"""
        basket_count = 0
        
        if self.zones_lines_config:
            # 존-라인 설정이 있으면 라인별로 랜덤 개수 배분
            for zone_config in self.zones_lines_config:
                zone_id = zone_config['zone_id']
                lines = zone_config.get('lines', [])
                
                for line_info in lines:
                    # line_info는 dict: {'line_id': 'A', 'length': 1000}
                    if isinstance(line_info, dict):
                        line_id = line_info.get('line_id')
                        line_length_cm = line_info.get('length', 0) * 100  # m → cm 변환
                    else:
                        # 하위 호환성: 문자열인 경우
                        line_id = line_info
                        line_length_cm = float('inf')  # 길이 제약 없음
                    
                    # 라인 길이 내에서 가능한 최대 바스켓 개수
                    max_baskets_in_line = int(line_length_cm / BASKET_WIDTH_CM) if line_length_cm > 0 else 0
                    
                    # 실제 배치 개수는 (최대값의 50%~90%) + 랜덤
                    if max_baskets_in_line > 0:
                        min_baskets = max(1, int(max_baskets_in_line * 0.5))
                        max_baskets = int(max_baskets_in_line * 0.9)
                        line_basket_count = random.randint(min_baskets, max(min_baskets, max_baskets))
                    else:
                        line_basket_count = 0
                    
                    for i in range(line_basket_count):
                        if basket_count >= self.pool_size:
                            break
                        
                        basket_count += 1
                        basket_id = f"BASKET-{basket_count:05d}"
                        self.baskets[basket_id] = {
                            "basket_id": basket_id,
                            "zone_id": zone_id,
                            "line_id": line_id,
                            "width_cm": BASKET_WIDTH_CM,
                            "destination": None,
                            "status": "available",  # available, in_transit, arrived
                            "assigned_at": None,
                            "updated_at": datetime.now().isoformat()
                        }
                    
                    if basket_count >= self.pool_size:
                        break
                
                if basket_count >= self.pool_size:
                    break
        else:
            # 설정이 없으면 기본적으로 전체 개수만 생성
            for i in range(1, self.pool_size + 1):
                basket_id = f"BASKET-{i:05d}"
                self.baskets[basket_id] = {
                    "basket_id": basket_id,
                    "zone_id": None,
                    "line_id": None,
                    "width_cm": BASKET_WIDTH_CM,
                    "destination": None,
                    "status": "available",
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
