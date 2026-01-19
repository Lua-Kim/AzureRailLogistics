import random
from typing import Dict, Optional


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
                "destination": None
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
