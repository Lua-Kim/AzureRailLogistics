import json
import random
from datetime import datetime
from enum import Enum

# 구역 설정 (메가FC 기준)
ZONES = [
    {"zone_id": "IB-01", "zone_name": "입고", "lines": 4, "length": 50, "sensors": 40},
    {"zone_id": "IS-01", "zone_name": "검수", "lines": 4, "length": 30, "sensors": 50},
    {"zone_id": "ST-RC", "zone_name": "랙 보관", "lines": 20, "length": 120, "sensors": 300},
    {"zone_id": "PK-01", "zone_name": "피킹", "lines": 12, "length": 100, "sensors": 200},
    {"zone_id": "PC-01", "zone_name": "가공", "lines": 3, "length": 40, "sensors": 50},
    {"zone_id": "SR-01", "zone_name": "분류", "lines": 8, "length": 80, "sensors": 160},
    {"zone_id": "OB-01", "zone_name": "출고", "lines": 4, "length": 60, "sensors": 40},
]

class Direction(Enum):
    FORWARD = "FORWARD"
    STOP = "STOP"

class Status(Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"


class SensorDataGenerator:
    """가상센서 데이터 생성 클래스"""
    
    def __init__(self):
        self.zones = ZONES
        self.basket_counter = 1
        self.active_baskets = {}  # 현재 이동 중인 바스켓
    
    def generate_sensor_id(self, zone_id: str, sensor_number: int) -> str:
        """센서 ID 생성"""
        zone_prefix = zone_id.replace("-", "")
        return f"SENSOR-{zone_prefix}{sensor_number:05d}"
    
    def generate_line_id(self, zone_id: str, line_number: int) -> str:
        """라인 ID 생성"""
        return f"{zone_id}-{line_number:03d}"
    
    def get_zone_sensors(self, zone_id: str) -> list:
        """특정 구역의 센서 목록 반환"""
        zone = next((z for z in self.zones if z["zone_id"] == zone_id), None)
        if not zone:
            return []
        
        sensors = []
        for i in range(1, zone["sensors"] + 1):
            sensors.append({
                "sensor_id": self.generate_sensor_id(zone_id, i),
                "line_number": (i - 1) % zone["lines"] + 1
            })
        return sensors
    
    def generate_single_event(self, zone_id: str, sensor_info: dict, is_moving: bool = False) -> dict:
        """단일 센서 이벤트 생성"""
        
        # 이동 여부에 따른 데이터 생성
        if is_moving:
            signal = True
            direction = Direction.FORWARD.value
            speed = random.uniform(1.5, 3.0)
            basket_id = random.choice(list(self.active_baskets.keys())) if self.active_baskets else None
            basket_weight = random.uniform(10.0, 25.0)
        else:
            signal = False
            direction = Direction.STOP.value
            speed = 0.0
            basket_id = None
            basket_weight = 0.0

        event = {
            "zone_id": zone_id,
            "line_id": self.generate_line_id(zone_id, sensor_info["line_number"]),
            "sensor_id": sensor_info["sensor_id"],
            "signal": signal,
            "direction": direction,
            "speed": round(speed, 2),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        return event
    
    def generate_zone_events(self, zone_id: str, event_count: int = None) -> list:
        """특정 구역의 모든 센서 이벤트 생성"""
        zone = next((z for z in self.zones if z["zone_id"] == zone_id), None)
        if not zone:
            return []
        
        # 기본값: 활성 센서는 전체의 30~50%
        if event_count is None:
            event_count = random.randint(int(zone["sensors"] * 0.3), int(zone["sensors"] * 0.5))
        
        sensors = self.get_zone_sensors(zone_id)
        active_sensors = random.sample(sensors, min(event_count, len(sensors)))
        
        events = []
        for sensor_info in active_sensors:
            is_moving = random.random() < 0.6  # 60% 확률로 이동 중
            event = self.generate_single_event(zone_id, sensor_info, is_moving)
            events.append(event)
        
        return events
    
    def generate_all_zones_events(self) -> list:
        """모든 구역의 센서 이벤트 생성"""
        all_events = []
        for zone in self.zones:
            zone_events = self.generate_zone_events(zone["zone_id"])
            all_events.extend(zone_events)
        
        return all_events
    
    def generate_batch(self, batch_size: int = 10) -> list:
        """배치 단위로 센서 데이터 생성"""
        batch = []
        for _ in range(batch_size):
            # 임의의 구역 선택
            zone = random.choice(self.zones)
            events = self.generate_zone_events(zone["zone_id"], event_count=random.randint(1, 5))
            batch.extend(events)
        
        return batch


# 테스트
if __name__ == "__main__":
    generator = SensorDataGenerator()
    
    # 1. 단일 구역의 이벤트 생성
    print("=== 입고(IB-01) 구역 이벤트 ===")
    ib_events = generator.generate_zone_events("IB-01", event_count=10)
    print(json.dumps(ib_events[:10], indent=2, ensure_ascii=False))
    
    # 2. 모든 구역의 이벤트 생성
    print("\n=== 모든 구역 이벤트 (샘플) ===")
    all_events = generator.generate_all_zones_events()
    print(f"총 이벤트: {len(all_events)}개")
    print(json.dumps(all_events[:5], indent=2, ensure_ascii=False))
    
    # 3. 배치 생성
    print("\n=== 배치 데이터 (크기: 20) ===")
    batch = generator.generate_batch(batch_size=20)
    print(f"배치 이벤트: {len(batch)}개")
