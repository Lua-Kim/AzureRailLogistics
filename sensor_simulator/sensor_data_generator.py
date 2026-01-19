import json
import random
import time
from datetime import datetime
from enum import Enum
from kafka import KafkaProducer
import threading
from database import get_db, ZoneDataDB

# ZONES는 데이터베이스에서 동적으로 로드
ZONES = []

class Direction(Enum):
    FORWARD = "FORWARD"
    STOP = "STOP"


class SensorDataGenerator:
    """가상센서 데이터 생성 클래스"""
    
    def __init__(self):
        global ZONES
        if not ZONES:
            self._load_zones_from_db()
        self.zones = ZONES
        self.is_running = True
        self.producer = None
        self.stream_thread = None
        self.lock = threading.Lock()
    
    def _load_zones_from_db(self):
        """데이터베이스에서 ZONES 설정 로드"""
        global ZONES
        try:
            db = next(get_db())
            zones_config = ZoneDataDB.get_zones_config_for_sensor(db)
            
            print(f"[센서 시뮬레이션] ========== DB에서 존 정보 로드 ==========")
            print(f"[센서 시뮬레이션] 조회된 존: {len(zones_config)}개")
            
            # DB에서 가져온 데이터를 ZONES 포맷으로 변환
            ZONES = []
            total_sensors = 0
            for zone in zones_config:
                zone_data = {
                    "zone_id": zone["zone_id"],
                    "zone_name": zone["zone_name"],
                    "lines": zone["lines"],
                    "length": zone["length"],
                    "sensors": zone["sensors"]
                }
                ZONES.append(zone_data)
                total_sensors += zone["sensors"]
                print(f"  ✓ {zone['zone_id']} ({zone['zone_name']})")
                print(f"    - 라인: {zone['lines']}개, 길이: {zone['length']}m, 센서: {zone['sensors']}개")
            
            print(f"[센서 시뮬레이션] ========== 로드 완료 ==========")
            print(f"[센서 시뮬레이션] 총 센서: {total_sensors}개")
            
        except Exception as e:
            print(f"[센서 시뮬레이션] ❌ DB 로드 실패: {e}")
            import traceback
            traceback.print_exc()
            raise
    
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
    
    def _stream_worker(self, bootstrap_servers='localhost:9092', topic='sensor-events', signal_probability: float = 0.6, speed_percent: float = 50.0):
        """실제 스트리밍을 수행하는 워커 스레드"""
        try:
            if not self.producer:
                self.producer = KafkaProducer(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
                )
            
            print(f"[센서 시뮬레이션] Kafka 연결: {bootstrap_servers}, Topic: {topic}")
            print(f"[센서 시뮬레이션] 총 센서: {sum(z['sensors'] for z in self.zones)}개")
            
            while self.is_running:
                events_sent = 0
                
                # 모든 구역의 모든 센서에서 이벤트 생성
                for zone in self.zones:
                    zone_id = zone["zone_id"]
                    sensors = self.get_zone_sensors(zone_id)
                    
                    for sensor_info in sensors:
                        if not self.is_running:
                            break
                        
                        event = self.generate_single_event(zone_id, sensor_info, signal_probability, speed_percent)
                        self.producer.send(topic, event)
                        events_sent += 1
                    
                    if not self.is_running:
                        break
                
                if self.is_running:
                    time.sleep(1)
                    
        except Exception as e:
            print(f"[센서 시뮬레이션 오류] {e}")
        finally:
            if self.producer:
                self.producer.flush()
            self.is_running = False
            print("[센서 시뮬레이션] 스트리밍 종료")
    
    def stream_to_kafka(self, bootstrap_servers='localhost:9092', topic='sensor-events', signal_probability: float = 0.6, speed_percent: float = 50.0):
        """Kafka로 센서 데이터 스트리밍 (메인 스레드에서 호출)
        
        Args:
            bootstrap_servers: Kafka 부트스트랩 서버
            topic: Kafka 토픽명
            signal_probability: signal이 true일 확률 (0.0 ~ 1.0, 기본값: 0.6)
            speed_percent: 속도 퍼센트 (0 ~ 100, 기본값: 50)
        """
        self._stream_worker(bootstrap_servers, topic, signal_probability, speed_percent)
    
    def start(self, bootstrap_servers='localhost:9092', topic='sensor-events', signal_probability: float = 0.6, speed_percent: float = 50.0):
        """스트리밍 시작 (별도 스레드에서)"""
        with self.lock:
            if self.is_running:
                return False
            
            self.is_running = True
            self.stream_thread = threading.Thread(
                target=self._stream_worker,
                args=(bootstrap_servers, topic, signal_probability, speed_percent),
                daemon=True
            )
            self.stream_thread.start()
            return True
    
    def stop(self):
        """스트리밍 중지"""
        with self.lock:
            if not self.is_running:
                return False
            
            self.is_running = False
            return True


# 테스트
if __name__ == "__main__":
    generator = SensorDataGenerator()
    
    # Kafka 스트리밍 시작
    generator.stream_to_kafka()
