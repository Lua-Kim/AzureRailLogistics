import json
import random
import time
from datetime import datetime
from enum import Enum
from kafka import KafkaProducer

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


class SensorDataGenerator:
    """가상센서 데이터 생성 클래스"""
    
    def __init__(self):
        self.zones = ZONES
    
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
    
    def generate_single_event(self, zone_id: str, sensor_info: dict, signal_probability: float = 0.6, speed_percent: float = 50.0) -> dict:
        """단일 센서 이벤트 생성
        
        Args:
            zone_id: 구역 ID
            sensor_info: 센서 정보
            signal_probability: signal이 true일 확률 (0.0 ~ 1.0)
            speed_percent: 속도 퍼센트 (0 ~ 100)
        """
        
        # 이동 여부 결정
        is_moving = random.random() < signal_probability
        
        if is_moving:
            signal = True
            direction = Direction.FORWARD.value
            max_speed = 100.0
            speed = round(max_speed * (speed_percent / 100), 2)
        else:
            signal = False
            direction = Direction.STOP.value
            speed = 0.0

        event = {
            "zone_id": zone_id,
            "line_id": self.generate_line_id(zone_id, sensor_info["line_number"]),
            "sensor_id": sensor_info["sensor_id"],
            "signal": signal,
            "direction": direction,
            "speed": speed,
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
            event = self.generate_single_event(zone_id, sensor_info)
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
    
    def stream_to_kafka(self, bootstrap_servers='localhost:9092', topic='sensor-events', signal_probability: float = 0.6, speed_percent: float = 50.0):
        """Kafka로 센서 데이터 스트리밍
        
        Args:
            bootstrap_servers: Kafka 부트스트랩 서버
            topic: Kafka 토픽명
            signal_probability: signal이 true일 확률 (0.0 ~ 1.0, 기본값: 0.6)
            speed_percent: 속도 퍼센트 (0 ~ 100, 기본값: 50)
        """
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
        )
        
        try:
            print(f"Kafka 연결됨: {bootstrap_servers}")
            print(f"Topic: {topic}")
            print(f"Signal 확률: {signal_probability * 100:.0f}%")
            print(f"속도: {speed_percent}% (최대 100.0 %)")
            print("센서 데이터 스트리밍 시작...\n")
            print(f"총 센서: {sum(z['sensors'] for z in self.zones)}개\n")
            
            while True:
                events_sent = 0
                
                # 모든 구역의 모든 센서에서 이벤트 생성
                for zone in self.zones:
                    zone_id = zone["zone_id"]
                    sensors = self.get_zone_sensors(zone_id)
                    
                    for sensor_info in sensors:
                        event = self.generate_single_event(zone_id, sensor_info, signal_probability, speed_percent)
                        producer.send(topic, event)
                        events_sent += 1
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {events_sent}개 이벤트 전송")
                
                # 1초 대기
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n스트리밍 중지")
        finally:
            producer.close()


# 테스트
if __name__ == "__main__":
    generator = SensorDataGenerator()
    
    # Kafka 스트리밍 시작
    generator.stream_to_kafka()
