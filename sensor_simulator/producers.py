# sensor_simulator/producers.py
import json
from abc import ABC, abstractmethod
from .websocket_server import WebSocketServer

# --- Abstract Base Class for DataProducers ---

class DataProducer(ABC):
    """모든 데이터 프로듀서가 따라야 하는 추상 베이스 클래스입니다."""
    
    @abstractmethod
    def send_data(self, data):
        """데이터를 특정 대상으로 전송합니다."""
        pass

    @abstractmethod
    def close(self):
        """프로듀서의 리소스를 정리하고 연결을 닫습니다."""
        pass

# --- Concrete Implementations ---

class PrintProducer(DataProducer):
    """데이터를 콘솔에 출력하는 간단한 프로듀서입니다."""
    
    def send_data(self, data):
        print(f"[PrintProducer]: {json.dumps(data, indent=2)}")

    def close(self):
        print("[PrintProducer]: Closed.")

class KafkaProducer(DataProducer):
    """Kafka 토픽으로 데이터를 전송하는 프로듀서입니다."""
    
    def __init__(self, bootstrap_servers, topic):
        # This is a mock implementation.
        self.topic = topic
        print(f"Initialized KafkaProducer for topic '{topic}' at {bootstrap_servers}")

    def send_data(self, data):
        print(f"Sending to Kafka topic '{self.topic}': {json.dumps(data)}")

    def close(self):
        print("KafkaProducer closed.")

class WebSocketProducer(DataProducer):
    """WebSocket 서버를 통해 데이터를 전송하는 프로듀서입니다."""
    
    def __init__(self, server: WebSocketServer):
        self.server = server
        print("Initialized WebSocketProducer.")

    def send_data(self, data):
        # 웹소켓 서버의 큐에 데이터를 넣습니다.
        self.server.send_data(data)

    def close(self):
        # 서버 중지는 메인 스크립트에서 처리합니다.
        print("WebSocketProducer closed.")
        
# --- Factory Function ---

def get_producer(config, **kwargs) -> DataProducer:
    """설정 파일(config)을 기반으로 적절한 프로듀서 인스턴스를 생성하고 반환합니다."""
    
    producer_type = getattr(config, 'PRODUCER_TYPE', 'print').lower()

    if producer_type == 'kafka':
        kafka_cfg = getattr(config, 'KAFKA_CONFIG', {})
        return KafkaProducer(
            bootstrap_servers=kafka_cfg.get('bootstrap_servers', 'localhost:9092'),
            topic=kafka_cfg.get('topic', 'default-topic')
        )
    
    elif producer_type == 'websocket':
        ws_server = kwargs.get('ws_server')
        if not ws_server:
            raise ValueError("WebSocketProducer requires a 'ws_server' instance.")
        return WebSocketProducer(ws_server)

    else:
        print(f"Unknown or unspecified producer type. Using PrintProducer as default.")
        return PrintProducer()
