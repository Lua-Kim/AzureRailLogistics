"""
개선된 센서 데이터 생성기

바스켓 이동 없이 순수 랜덤 센서 데이터만 생성
"""

import json
import random
import time
from datetime import datetime
from enum import Enum
from kafka import KafkaProducer
import threading

from sensor_db import get_db, ZoneDataDB

class Direction(Enum):
    FORWARD = "FORWARD"
    STOP = "STOP"


class SimpleSensorDataGenerator:
    """간단한 센서 데이터 생성 클래스 (바스켓 이동 없음)"""
    
    def __init__(self):
        """초기화"""
        self.zones = []
        self.is_running = False
        self.producer = None
        self.stream_thread = None
        self.lock = threading.Lock()
        
        # DB에서 존 정보 로드
        self._load_zones_from_db()
    
    def _load_zones_from_db(self):
        """데이터베이스에서 ZONES 설정 로드"""
        try:
            db = next(get_db())
            zones_config = ZoneDataDB.get_zones_config_for_sensor(db)
            
            print(f"[센서 생성기] ========== DB에서 존 정보 로드 ==========")
            print(f"[센서 생성기] 조회된 존: {len(zones_config)}개")
            
            # DB에서 가져온 데이터를 ZONES 포맷으로 변환
            self.zones = []
            total_sensors = 0
            for zone in zones_config:
                zone_data = {
                    "zone_id": zone["zone_id"],
                    "zone_name": zone["zone_name"],
                    "lines": zone["lines"],
                    "length": zone["length"],
                    "sensors": zone["sensors"]
                }
                self.zones.append(zone_data)
                total_sensors += zone["sensors"]
                print(f"  ✓ {zone['zone_id']} ({zone['zone_name']})")
                print(f"    - 라인: {zone['lines']}개, 길이: {zone['length']}m, 센서: {zone['sensors']}개")
            
            print(f"[센서 생성기] ========== 로드 완료 ==========")
            print(f"[센서 생성기] 총 센서: {total_sensors}개")
            
        except Exception as e:
            print(f"[센서 생성기] ❌ DB 로드 실패: {e}")
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
        """단일 센서 이벤트 생성"""
        
        line_id = self.generate_line_id(zone_id, sensor_info["line_number"])
        sensor_id = sensor_info["sensor_id"]
        
        # 신호 확률 기반 신호 결정 (랜덤)
        signal = random.random() < signal_probability
        
        # 신호에 따른 방향/속도 설정
        if signal:
            direction = Direction.FORWARD.value
            max_speed = 100.0
            speed = round(max_speed * (speed_percent / 100), 2)
        else:
            direction = Direction.STOP.value
            speed = 0.0

        event = {
            "zone_id": zone_id,
            "line_id": line_id,
            "sensor_id": sensor_id,
            "signal": signal,
            "direction": direction,
            "speed": speed,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        return event
    
    def _stream_worker(self, bootstrap_servers='localhost:9092', topic='sensor-events', signal_probability: float = 0.6, speed_percent: float = 50.0):
        """실제 스트리밍을 수행하는 워커 스레드"""
        try:
            if not self.producer:
                self.producer = KafkaProducer(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
                )
            
            print(f"[센서 생성기] Kafka 연결: {bootstrap_servers}, Topic: {topic}")
            print(f"[센서 생성기] 신호 확률: {signal_probability}, 속도: {speed_percent}%")
            print(f"[센서 생성기] 총 센서: {sum(z['sensors'] for z in self.zones)}개")
            print(f"[센서 생성기] 데이터 생성 시작...")
            
            cycle_count = 0
            while self.is_running:
                events_sent = 0
                cycle_count += 1
                
                # 모든 구역의 모든 센서에서 이벤트 생성
                for zone in self.zones:
                    if not self.is_running:
                        break
                        
                    zone_id = zone["zone_id"]
                    sensors = self.get_zone_sensors(zone_id)
                    
                    for sensor_info in sensors:
                        if not self.is_running:
                            break
                        
                        event = self.generate_single_event(zone_id, sensor_info, signal_probability, speed_percent)
                        self.producer.send(topic, event)
                        events_sent += 1
                
                if self.is_running:
                    print(f"[센서 생성기] 사이클 {cycle_count}: {events_sent}개 이벤트 발송")
                    time.sleep(1)
                    
        except Exception as e:
            print(f"[센서 생성기] ❌ 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.producer:
                self.producer.flush()
            self.is_running = False
            print("[센서 생성기] 스트리밍 종료")
    
    def start(self, bootstrap_servers='localhost:9092', topic='sensor-events', signal_probability: float = 0.6, speed_percent: float = 50.0):
        """스트리밍 시작 (별도 스레드에서)"""
        with self.lock:
            if self.is_running:
                print("[센서 생성기] ⚠️ 이미 실행 중입니다")
                return False
            
            self.is_running = True
            
            self.stream_thread = threading.Thread(
                target=self._stream_worker,
                args=(bootstrap_servers, topic, signal_probability, speed_percent),
                daemon=False
            )
            self.stream_thread.start()
            print("[센서 생성기] ✓ 스트리밍 시작됨")
            return True
    
    def stop(self):
        """스트리밍 중지"""
        with self.lock:
            if not self.is_running:
                print("[센서 생성기] ⚠️ 실행 중이 아닙니다")
                return False
            
            self.is_running = False
            print("[센서 생성기] 스트리밍 중지 신호 전송")
            return True


if __name__ == "__main__":
    generator = SimpleSensorDataGenerator()
    generator.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n사용자가 중지함")
        generator.stop()
