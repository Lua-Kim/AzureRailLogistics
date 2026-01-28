"""실제 센서 어댑터 - 실제 센서 시스템 연동 (스켈레톤)"""

from .base import SensorAdapter
# from kafka import KafkaProducer  # Not used in IoT Hub integration
import json
from datetime import datetime


class RealSensorAdapter(SensorAdapter):
    """실제 센서 시스템 어댑터 (구현 예시)"""
    
    def __init__(self, sensor_config: dict):
        """
        Args:
            sensor_config: {
                "gateway_url": str,  # 센서 게이트웨이 URL
                "protocol": str,     # MQTT/REST/WebSocket
                "kafka_broker": str,
                "polling_interval": int
            }
        """
        self.config = sensor_config
        self.is_running = False
        
        # Kafka Producer 초기화 (Not used in IoT Hub integration)
        # self.kafka_producer = KafkaProducer(
        #     bootstrap_servers=[sensor_config.get("kafka_broker", "localhost:9092")],
        #     value_serializer=lambda x: json.dumps(x).encode('utf-8')
        # )
        self.kafka_producer = None
        
        print(f"[RealSensorAdapter] 초기화: {sensor_config.get('gateway_url')}")
    
    def start(self) -> bool:
        """실제 센서 데이터 수집 시작"""
        if self.is_running:
            return False
        
        try:
            # TODO: 실제 센서 게이트웨이 연결
            # 예: MQTT 구독, REST 폴링, WebSocket 연결
            
            print("[RealSensorAdapter] ✅ 실제 센서 연결 시작")
            print("  → 센서 게이트웨이에서 데이터 수신 대기")
            print("  → Kafka 토픽 'sensor-events'로 전송")
            
            self.is_running = True
            return True
        except Exception as e:
            print(f"[RealSensorAdapter] ❌ 시작 실패: {e}")
            return False
    
    def stop(self) -> bool:
        """실제 센서 데이터 수집 중지"""
        if not self.is_running:
            return False
        
        try:
            # TODO: 센서 게이트웨이 연결 해제
            
            self.kafka_producer.close()
            self.is_running = False
            print("[RealSensorAdapter] ✅ 실제 센서 연결 종료")
            return True
        except Exception as e:
            print(f"[RealSensorAdapter] ❌ 중지 실패: {e}")
            return False
    
    def get_status(self) -> dict:
        """실제 센서 상태 조회"""
        return {
            "running": self.is_running,
            "source_type": "real_sensor",
            "events_count": 0,
            "gateway_url": self.config.get("gateway_url", "N/A")
        }
    
    def reset(self) -> bool:
        """실제 센서는 리셋 불가"""
        print("[RealSensorAdapter] ⚠️ 실제 센서는 리셋할 수 없습니다")
        return False
    
    def _convert_sensor_data_to_kafka_event(self, raw_sensor_data: dict) -> dict:
        """실제 센서 데이터를 Kafka 이벤트 포맷으로 변환
        
        실제 구현 시 센서 프로토콜에 맞게 수정 필요
        
        Args:
            raw_sensor_data: 센서에서 받은 원본 데이터
        
        Returns:
            dict: Kafka 표준 포맷
        """
        return {
            "zone_id": raw_sensor_data.get("zone"),
            "line_id": raw_sensor_data.get("line"),
            "sensor_id": raw_sensor_data.get("sensor_id"),
            "signal": raw_sensor_data.get("detected", False),
            "timestamp": datetime.now().isoformat(),
            "speed": raw_sensor_data.get("conveyor_speed", 0.0)
        }
    
    def _publish_to_kafka(self, event: dict):
        """Kafka로 이벤트 전송"""
        try:
            self.kafka_producer.send('sensor-events', event)
        except Exception as e:
            print(f"[RealSensorAdapter] Kafka 전송 실패: {e}")
