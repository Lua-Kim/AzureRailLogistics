import random
from typing import Dict, Optional, List
from datetime import datetime
import threading

# 바스켓 설정
BASKET_WIDTH_CM = 50  # 바스켓 폭 (cm)


class BasketPool:
    """바스켓 풀 관리 클래스 (Thread-Safe)"""
    
    def __init__(self, pool_size: int = 100, zones_lines_config: Optional[List[dict]] = None):
        """
        Args:
            pool_size: 바스켓 풀 크기
            zones_lines_config: 존-라인 설정 (라인별로 바스켓을 배분하고 싶을 때)
        """
        self.pool_size = pool_size
        self.zones_lines_config = zones_lines_config or []
        self.baskets = {}
        self.lock = threading.RLock()
        self._initialize_pool()

    def _initialize_pool(self):
        """바스켓 풀 초기화"""
        with self.lock:
            for i in range(self.pool_size):
                basket_id = f"BASKET-{i+1:05d}"
                self.baskets[basket_id] = {
                    "basket_id": basket_id,
                    "status": "available",
                    "zone_id": None,
                    "line_id": None,
                    "destination": None,
                    "width_cm": BASKET_WIDTH_CM,
                    "created_at": datetime.now().isoformat()
                }

    def get_all_baskets(self) -> Dict:
        """모든 바스켓 조회"""
        with self.lock:
            return self.baskets.copy()

    def get_basket(self, basket_id: str) -> Optional[dict]:
        """특정 바스켓 조회"""
        with self.lock:
            return self.baskets.get(basket_id)

    def get_available_baskets(self) -> List[dict]:
        """사용 가능한 바스켓 목록 조회"""
        with self.lock:
            return [b for b in self.baskets.values() if b["status"] == "available"]

    def get_baskets_by_status(self, status: str) -> List[dict]:
        """상태별 바스켓 목록 조회"""
        with self.lock:
            return [b for b in self.baskets.values() if b["status"] == status]

    def assign_basket(self, basket_id: str, zone_id: str, line_id: str, destination: str = None) -> Optional[dict]:
        """바스켓 할당 (available -> in_transit)"""
        with self.lock:
            if basket_id not in self.baskets:
                return None
            
            basket = self.baskets[basket_id]
            basket["status"] = "in_transit"
            basket["zone_id"] = zone_id
            basket["line_id"] = line_id
            basket["destination"] = destination
            basket["assigned_at"] = datetime.now().isoformat()
            return basket

    def update_basket_status(self, basket_id: str, status: str, zone_id: str = None, line_id: str = None):
        """바스켓 상태 업데이트"""
        with self.lock:
            if basket_id not in self.baskets:
                return
            
            basket = self.baskets[basket_id]
            basket["status"] = status
            if zone_id: basket["zone_id"] = zone_id
            if line_id: basket["line_id"] = line_id
            basket["updated_at"] = datetime.now().isoformat()

    def get_statistics(self) -> dict:
        """바스켓 통계 조회"""
        with self.lock:
            total = len(self.baskets)
            available = sum(1 for b in self.baskets.values() if b["status"] == "available")
            in_transit = sum(1 for b in self.baskets.values() if b["status"] == "in_transit")
            arrived = sum(1 for b in self.baskets.values() if b["status"] == "arrived")
            return {
                "total": total,
                "available": available,
                "in_transit": in_transit,
                "arrived": arrived
            }

    def expand_pool(self, additional_count: int):
        """바스켓 풀 크기 동적 확장"""
        # lock이 없으면 생성 (안전장치)
        if not hasattr(self, 'lock'):
            self.lock = threading.Lock()
            
        with self.lock:
            current_count = len(self.baskets)
            for i in range(additional_count):
                basket_id = f"BASKET-{current_count + i + 1:05d}"
                self.baskets[basket_id] = {
                    "basket_id": basket_id,
                    "status": "available",
                    "zone_id": None,
                    "line_id": None,
                    "destination": None,
                    "width_cm": BASKET_WIDTH_CM,
                    "created_at": datetime.now().isoformat()
                }
            self.pool_size += additional_count
            print(f"[BasketPool] 풀 확장: {additional_count}개 추가 (총 {self.pool_size}개)")