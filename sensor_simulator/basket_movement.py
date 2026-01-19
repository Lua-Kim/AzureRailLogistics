import threading
import time
from datetime import datetime
from typing import Dict, List
from sensor_db import get_db, ZoneDataDB

"""
바스켓 이동 시뮬레이터

1초마다 각 바스켓의 위치를 계산하고 업데이트합니다.
- 바스켓이 라인을 따라 이동
- 라인 끝에 도달하면 상태를 "arrived"로 변경
- 동시성 관리를 위해 lock 사용
"""


class BasketMovement:
    """바스켓 이동 관리 클래스"""
    
    # 기본 통과 시간 (초)
    DEFAULT_TRANSIT_TIME = 50.0
    
    def __init__(self, basket_pool, zones):
        """
        Args:
            basket_pool: BasketPool 인스턴스
            zones: ZONES 설정 리스트
                [
                    {
                        "zone_id": "IB-01",
                        "zone_name": "입고",
                        "lines": 4,
                        "length": 50,
                        "sensors": 40
                    },
                    ...
                ]
        """
        self.basket_pool = basket_pool
        self.zones = zones
        self.is_running = False
        self.movement_thread = None
        self.lock = threading.Lock()
        
        # 바스켓별 위치 추적 (basket_id → position_meters)
        self.basket_positions: Dict[str, float] = {}
        
        # 바스켓별 라인 정보 (basket_id → {zone_id, line_id, line_length})
        self.basket_lines: Dict[str, dict] = {}
        
        # 통과 시간 (초) - 나중에 프론트에서 변경 가능
        self.transit_time = self.DEFAULT_TRANSIT_TIME
    
    def start(self):
        """바스켓 이동 시뮬레이션 시작"""
        if self.is_running:
            print("[바스켓 이동] 이미 실행 중입니다")
            return False
        
        with self.lock:
            self.is_running = True
            self.movement_thread = threading.Thread(
                target=self._movement_worker,
                daemon=True,
                name="BasketMovementWorker"
            )
            self.movement_thread.start()
        
        print("[바스켓 이동] ========== 바스켓 이동 시뮬레이터 시작 ==========")
        print(f"[바스켓 이동] 통과 시간: {self.transit_time}초")
        return True
    
    def stop(self):
        """바스켓 이동 시뮬레이션 중지"""
        with self.lock:
            if not self.is_running:
                return False
            
            self.is_running = False
        
        print("[바스켓 이동] 바스켓 이동 시뮬레이터 중지")
        return True
    
    def set_transit_time(self, transit_time: float):
        """
        바스켓 통과 시간 설정 (프론트엔드에서 호출)
        
        Args:
            transit_time: 라인 통과 시간 (초)
        """
        with self.lock:
            self.transit_time = transit_time
        print(f"[바스켓 이동] 통과 시간 변경: {transit_time}초")
    
    def _movement_worker(self):
        """메인 이동 루프 - 1초마다 실행"""
        try:
            while self.is_running:
                self._update_basket_positions()
                time.sleep(1)
        
        except Exception as e:
            print(f"[바스켓 이동] ❌ 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_running = False
            print("[바스켓 이동] 이동 워커 종료")
    
    def _update_basket_positions(self):
        """모든 바스켓의 위치 업데이트"""
        try:
            in_transit_baskets = self.basket_pool.get_baskets_by_status("in_transit")
            
            if not in_transit_baskets:
                return
            
            for basket in in_transit_baskets:
                self._move_basket(basket)
        
        except Exception as e:
            print(f"[바스켓 이동] 위치 업데이트 오류: {e}")
    
    def _move_basket(self, basket: dict):
        """단일 바스켓의 위치 계산 및 이동"""
        basket_id = basket["basket_id"]
        zone_id = basket["zone_id"]
        line_id = basket["line_id"]
        
        # 첫 진입: 위치 및 라인 정보 초기화
        if basket_id not in self.basket_positions:
            self.basket_positions[basket_id] = 0.0
            self.basket_lines[basket_id] = {
                "zone_id": zone_id,
                "line_id": line_id,
                "line_length": self._get_line_length(zone_id, line_id)
            }
        
        # 현재 위치 및 라인 정보 조회
        current_pos = self.basket_positions[basket_id]
        line_info = self.basket_lines[basket_id]
        line_length = line_info["line_length"]
        
        # 1초당 이동 거리 계산
        # 예: 50m을 50초에 통과 → 1m/초
        distance_per_second = line_length / self.transit_time
        
        # 새로운 위치 계산
        new_pos = current_pos + distance_per_second
        
        # 로깅 (10%마다)
        progress = int((new_pos / line_length) * 100)
        prev_progress = int((current_pos / line_length) * 100)
        if progress != prev_progress and progress % 10 == 0:
            print(f"[바스켓 이동] {basket_id}: {progress}% 진행 ({new_pos:.2f}m / {line_length}m)")
        
        # 라인 끝 도달
        if new_pos >= line_length:
            self._complete_basket_transit(basket_id, basket)
        else:
            # 위치 업데이트
            with self.lock:
                self.basket_positions[basket_id] = new_pos
    
    def _complete_basket_transit(self, basket_id: str, basket: dict):
        """바스켓이 라인을 완전히 통과"""
        zone_id = basket["zone_id"]
        line_id = basket["line_id"]
        
        print(f"[바스켓 이동] ✅ {basket_id} 라인 통과 완료 ({zone_id}/{line_id})")
        
        # 바스켓 상태 업데이트: in_transit → arrived
        with self.lock:
            self.basket_pool.update_basket_status(
                basket_id,
                "arrived",
                zone_id=zone_id,
                line_id=line_id
            )
            
            # 위치 정보 정리
            if basket_id in self.basket_positions:
                del self.basket_positions[basket_id]
            if basket_id in self.basket_lines:
                del self.basket_lines[basket_id]
    
    def _get_line_length(self, zone_id: str, line_id: str = "A") -> float:
        """라인의 정확한 길이를 데이터베이스에서 조회"""
        try:
            db = next(get_db())
            length = ZoneDataDB.get_line_length(db, zone_id, line_id)
            db.close()
            return length
        except Exception as e:
            print(f"[바스켓 이동] ⚠️ 라인 길이 조회 실패: {e}")
            return 50.0  # 기본값
    
    def get_basket_position(self, basket_id: str) -> dict:
        """바스켓의 현재 위치 조회"""
        with self.lock:
            if basket_id not in self.basket_positions:
                return None
            
            pos = self.basket_positions[basket_id]
            line_info = self.basket_lines.get(basket_id, {})
            
            return {
                "basket_id": basket_id,
                "position_meters": pos,
                "line_length": line_info.get("line_length", 0),
                "progress_percent": (pos / line_info.get("line_length", 1)) * 100 if line_info.get("line_length") else 0,
                "zone_id": line_info.get("zone_id"),
                "line_id": line_info.get("line_id"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    def get_all_positions(self) -> List[dict]:
        """모든 이동 중인 바스켓의 위치 조회"""
        with self.lock:
            positions = []
            for basket_id in self.basket_positions.keys():
                pos = self.get_basket_position(basket_id)
                if pos:
                    positions.append(pos)
            return positions
