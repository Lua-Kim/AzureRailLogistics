# sensor_simulator/config.py

# --- Producer Configuration ---
# 사용할 Producer 타입을 선택합니다. 'kafka', 'eventhubs', 또는 'websocket'
PRODUCER_TYPE = 'kafka'


# --- Kafka Configuration ---
KAFKA_CONFIG = {
    'bootstrap_servers': 'localhost:9092',  # Kafka 브로커 주소
    'topic': 'logistics-sensors'            # 전송할 토픽 이름
}


# --- Azure Event Hubs Configuration ---
# Event Hubs 사용 시 아래 값들을 채워야 합니다.
EVENTHUBS_CONFIG = {
    'connection_str': 'YOUR_EVENTHUBS_CONNECTION_STR',  # Event Hubs 네임스페이스 연결 문자열
    'eventhub_name': 'YOUR_EVENTHUB_NAME'              # 이벤트 허브 이름
}

# --- Traffic Simulation Parameters ---
# 물류량 변화에 영향을 미치는 외부 변수
TRAFFIC_PARAMETERS = {
    'order_quantity': 1000,   # 시간당 주문량 (예: 1000개)
    'inbound_quantity': 800,  # 시간당 입고되는 물품량
    'return_quantity': 50,    # 시간당 반품되는 물품량
    'workload': 70            # 현재 작업 부하 수준 (0-100%)
}
