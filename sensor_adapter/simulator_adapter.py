"""시뮬레이터 어댑터 - 기존 시뮬레이터를 표준 인터페이스로 감쌈"""

import sys
import os

# sensor_simulator 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sensor_simulator'))

from .base import SensorAdapter


class SimulatorAdapter(SensorAdapter):
    """가상 센서 시뮬레이터 어댑터"""
    
    def __init__(self, basket_pool, zones_config):
        """
        Args:
            basket_pool: BasketPool 인스턴스
            zones_config: 존 설정 리스트
        """
        from basket_manager import BasketPool
        from basket_movement import BasketMovement
        from sensor_data_generator import SensorDataGenerator
        
        self.basket_pool = basket_pool
        self.zones_config = zones_config
        
        # 바스켓 이동 시뮬레이터 초기화
        self.movement_simulator = BasketMovement(basket_pool, zones_config)
        
        # 센서 데이터 생성기 초기화
        self.sensor_generator = SensorDataGenerator(
            basket_pool=basket_pool,
            basket_movement=self.movement_simulator
        )
        
        self.is_running = False
    
    def start(self) -> bool:
        """시뮬레이터 시작"""
        if self.is_running:
            print("[SimulatorAdapter] 이미 실행 중입니다")
            return False
        
        try:
            # 바스켓 이동 시뮬레이터 시작
            self.movement_simulator.start()
            
            # 센서 데이터 생성기 시작
            self.sensor_generator.start()
            
            self.is_running = True
            print("[SimulatorAdapter] ✅ 시뮬레이터 시작 완료")
            return True
        except Exception as e:
            print(f"[SimulatorAdapter] ❌ 시작 실패: {e}")
            return False
    
    def stop(self) -> bool:
        """시뮬레이터 중지"""
        if not self.is_running:
            print("[SimulatorAdapter] 이미 중지 상태입니다")
            return False
        
        try:
            # 센서 생성기 중지
            self.sensor_generator.stop()
            
            # 바스켓 이동 시뮬레이터 중지
            self.movement_simulator.stop()
            
            self.is_running = False
            print("[SimulatorAdapter] ✅ 시뮬레이터 중지 완료")
            return True
        except Exception as e:
            print(f"[SimulatorAdapter] ❌ 중지 실패: {e}")
            return False
    
    def get_status(self) -> dict:
        """시뮬레이터 상태 조회"""
        line_speed_zones = {}
        if self.movement_simulator:
            with self.movement_simulator.lock:
                line_speed_zones = {
                    k: v[:] for k, v in self.movement_simulator.line_speed_zones.items()
                }
        
        return {
            "running": self.is_running,
            "source_type": "simulator",
            "events_count": 0,  # 필요시 추가
            "line_speed_zones": line_speed_zones
        }
    
    def reset(self) -> bool:
        """시뮬레이터 초기화 (바스켓 리셋)"""
        try:
            # 모든 바스켓을 available 상태로 리셋
            with self.basket_pool.lock:
                for basket_id, basket in self.basket_pool.baskets.items():
                    basket["status"] = "available"
                    basket["motion_state"] = "idle"
                    basket["is_bottleneck"] = False
                    basket["zone_id"] = None
                    basket["line_id"] = None
                    basket["destination"] = None
                    if "assigned_at" in basket:
                        del basket["assigned_at"]
                    if "updated_at" in basket:
                        del basket["updated_at"]
            
            # movement_simulator의 위치 정보도 초기화
            if self.movement_simulator:
                with self.movement_simulator.lock:
                    self.movement_simulator.basket_positions.clear()
                    self.movement_simulator.basket_lines.clear()
            
            print("[SimulatorAdapter] ✅ 초기화 완료")
            return True
        except Exception as e:
            print(f"[SimulatorAdapter] ❌ 초기화 실패: {e}")
            return False
    
    def get_movement_simulator(self):
        """바스켓 이동 시뮬레이터 인스턴스 반환 (호환성)"""
        return self.movement_simulator
