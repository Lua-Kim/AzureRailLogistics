# sensor_simulator/main.py

import asyncio
import datetime
import json
import time

# 프로젝트의 설정과 컴포넌트들을 import
import config
from producers import get_producer, DataProducer
from websocket_server import WebSocketServer
from sensor_generator import SensorGenerator
from aggregator import Aggregator # Aggregator 임포트

# "메가 풀필먼트 센터" 기준 Zone 설정
ZONES_CONFIG = [
    # Inbound Docks (Zone A)
    {'id': 'IN-A01', 'name': 'Inbound Dock A01', 'type': 'entry', 'lines': 4, 'length': 20, 'workers': 8, 'direction': 'Inbound'},
    {'id': 'IN-A02', 'name': 'Inbound Dock A02', 'type': 'entry', 'lines': 4, 'length': 20, 'workers': 8, 'direction': 'Inbound'},
    {'id': 'IN-A03', 'name': 'Inbound Dock A03', 'type': 'entry', 'lines': 4, 'length': 20, 'workers': 8, 'direction': 'Inbound'},

    # Sorting Area (Zone B)
    {'id': 'SRT-B01', 'name': 'Primary Sorter B01', 'type': 'sorting', 'lines': 8, 'length': 50, 'workers': 4, 'direction': 'Sorting-Flow'},
    {'id': 'SRT-B02', 'name': 'Secondary Sorter B02', 'type': 'sorting', 'lines': 16, 'length': 30, 'workers': 6, 'direction': 'Sorting-Flow'},

    # Buffer Storage (Zone C)
    {'id': 'BUF-C01', 'name': 'Buffer Storage C01', 'type': 'buffer', 'lines': 2, 'length': 100, 'workers': 2, 'direction': 'Buffer-Flow'},
    {'id': 'BUF-C02', 'name': 'Buffer Storage C02', 'type': 'buffer', 'lines': 2, 'length': 100, 'workers': 2, 'direction': 'Buffer-Flow'},

    # Picking Towers (Zone D, E, F)
    {'id': 'PCK-D01', 'name': 'Picking Tower D-1F', 'type': 'process', 'lines': 10, 'length': 40, 'workers': 15, 'direction': 'Processing-Flow'},
    {'id': 'PCK-D02', 'name': 'Picking Tower D-2F', 'type': 'process', 'lines': 10, 'length': 40, 'workers': 15, 'direction': 'Processing-Flow'},
    {'id': 'PCK-E01', 'name': 'Picking Tower E-1F', 'type': 'process', 'lines': 12, 'length': 40, 'workers': 18, 'direction': 'Processing-Flow'},
    {'id': 'PCK-E02', 'name': 'Picking Tower E-2F', 'type': 'process', 'lines': 12, 'length': 40, 'workers': 18, 'direction': 'Processing-Flow'},
    {'id': 'PCK-F01', 'name': 'Auto-Picker F-1F', 'type': 'process', 'lines': 5, 'length': 60, 'workers': 3, 'direction': 'Processing-Flow'},

    # Quality Control (Zone G)
    {'id': 'QC-G01', 'name': 'QC & Inspection G01', 'type': 'qc', 'lines': 3, 'length': 15, 'workers': 10, 'direction': 'QC-Flow'},
    {'id': 'QC-G02', 'name': 'QC & Inspection G02', 'type': 'qc', 'lines': 3, 'length': 15, 'workers': 10, 'direction': 'QC-Flow'},

    # Packing (Zone H)
    {'id': 'PAK-H01', 'name': 'Packing Station H01', 'type': 'process', 'lines': 8, 'length': 10, 'workers': 20, 'direction': 'Processing-Flow'},
    {'id': 'PAK-H02', 'name': 'Auto-Packer H02', 'type': 'process', 'lines': 4, 'length': 25, 'workers': 5, 'direction': 'Processing-Flow'},

    # Outbound Area (Zone I)
    {'id': 'OUT-I01', 'name': 'Outbound Sorter I01', 'type': 'sorting', 'lines': 12, 'length': 40, 'workers': 8, 'direction': 'Sorting-Flow'},
    {'id': 'OUT-I02', 'name': 'Outbound Dock I02', 'type': 'exit', 'lines': 6, 'length': 25, 'workers': 12, 'direction': 'Outbound'},
    {'id': 'OUT-I03', 'name': 'Outbound Dock I03', 'type': 'exit', 'lines': 6, 'length': 25, 'workers': 12, 'direction': 'Outbound'},
]

# 총 센서 수 계산
TOTAL_SENSORS = sum(zone['lines'] for zone in ZONES_CONFIG)
# 집계 데이터를 전송할 간격 (초)
AGGREGATION_INTERVAL_SECONDS = 5


async def main_orchestrator_loop(producer: DataProducer):
    """
    메인 오케스트레이터 루프:
    - 센서 이벤트를 계속 생성합니다.
    - pass_event가 1인 경우 Aggregator에 이벤트를 전달합니다.
    - 주기적으로 Aggregator로부터 집계된 데이터를 받아 Producer를 통해 전송합니다.
    - 각 센서가 대략 1초에 1번씩 데이터를 생성하도록 조절합니다.
    """
    sensor_generator = SensorGenerator(ZONES_CONFIG, config.TRAFFIC_PARAMETERS)
    aggregator = Aggregator(ZONES_CONFIG, AGGREGATION_INTERVAL_SECONDS) # Aggregator 초기화
    
    # 센서 데이터 생성기(제너레이터)를 가져옵니다.
    signal_iterator = sensor_generator.generate_sensor_data()
    
    last_aggregation_time = time.time() # 집계 타이밍을 위한 변수
    
    print(f"--- Starting Main Orchestrator Loop (Total sensors: {TOTAL_SENSORS}) ---")
    while True:
        # 1. 원시 센서 이벤트 생성
        sensor_event = next(signal_iterator)
        
        # 2. pass_event가 1인 경우에만 센서 이벤트를 Aggregator에 전달합니다.
        if sensor_event['pass_event'] == 1:
            aggregator.process_sensor_event(sensor_event)
            
        # 3. 주기적으로 집계된 데이터를 Producer를 통해 전송합니다.
        current_time = time.time()
        if current_time - last_aggregation_time >= AGGREGATION_INTERVAL_SECONDS:
            print(f"--- ({datetime.datetime.now()}) Aggregating and sending data ---")
            aggregated_data = aggregator.get_aggregated_data_and_clear_buffer()
            if aggregated_data:
                producer.send_data(aggregated_data)
                # print(f"Sent {len(aggregated_data)} aggregated sensor reports.") # Debugging line
                # print("Sample aggregated data:", json.dumps(aggregated_data[0], indent=2))
            else:
                print("No aggregated data to send in this interval.")
            last_aggregation_time = current_time
            
        # 각 센서가 대략 1초에 1번씩 데이터를 생성하도록 조절합니다.
        # 즉, 모든 센서가 한 바퀴 데이터를 생성하는 데 약 1초가 걸리도록 합니다.
        await asyncio.sleep(1 / TOTAL_SENSORS)


async def main():
    """메인 비동기 함수: 전체 시뮬레이션 환경을 설정하고 실행합니다."""
    producer = None
    ws_server = None
    try:
        # WebSocket 서버 설정 및 시작
        ws_server = WebSocketServer(host='localhost', port=8765)
        await ws_server.start()
        
        # 설정에 맞는 Producer 인스턴스 가져오기 (WebSocket 서버 인스턴스 전달)
        producer = get_producer(config, ws_server=ws_server)
        
        # 메인 오케스트레이터 루프 실행
        await main_orchestrator_loop(producer)

    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if producer:
            producer.close()
        if ws_server:
            await ws_server.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMain execution stopped.")