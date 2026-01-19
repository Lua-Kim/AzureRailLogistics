import json
from kafka import KafkaConsumer
from typing import List
import threading

class SensorEventConsumer:
    """Kafka에서 센서 이벤트를 수신하는 Consumer"""
    
    def __init__(self, bootstrap_servers='localhost:9092', topic='sensor-events'):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer = None
        self.latest_events = []  # 최근 이벤트 저장 (메모리)
        self.max_events = 2000  # 최대 2000개까지 유지 (그래프 표시용 버퍼 확대)
        self.is_running = False
        
    def start(self):
        """Consumer 시작"""
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',  # 최신 메시지부터 읽음
            enable_auto_commit=True
        )
        
        self.is_running = True
        print(f"Kafka Consumer 시작: {self.bootstrap_servers}, Topic: {self.topic}")
        
        # 백그라운드 스레드로 실행
        thread = threading.Thread(target=self._consume_loop, daemon=True)
        thread.start()
        
    def _consume_loop(self):
        """메시지 수신 루프"""
        for message in self.consumer:
            if not self.is_running:
                break
                
            event = message.value
            
            # 최근 이벤트 목록에 추가
            self.latest_events.append(event)
            
            # 최대 개수 유지
            if len(self.latest_events) > self.max_events:
                self.latest_events.pop(0)
                
    def get_latest_events(self, count: int = 10) -> List[dict]:
        """최근 이벤트 반환"""
        return self.latest_events[-count:]
    
    def get_event_count(self) -> int:
        """수신한 이벤트 총 개수"""
        return len(self.latest_events)
    
    def stop(self):
        """Consumer 중지"""
        self.is_running = False
        if self.consumer:
            self.consumer.close()
        print("Kafka Consumer 중지")
