# sensor_simulator/aggregator.py
import datetime
from collections import defaultdict

class Aggregator:
    """
    원시 센서 신호를 수집하여 의미 있는 Zone 단위의 데이터로 집계하는 클래스.
    """

    def __init__(self, zones_config):
        """
        Aggregator를 초기화합니다.

        :param zones_config: Zone 설정 정보가 담긴 리스트
        """
        self.zones_config = {zone['id']: zone for zone in zones_config}
        self.zone_data_buffer = defaultdict(lambda: defaultdict(list))
        print("Aggregator: Initialized.")

    def process_signal(self, signal: dict):
        """
        하나의 원시 센서 신호를 처리하여 내부 버퍼에 저장합니다.

        :param signal: 센서 생성기에서 온 단일 신호 데이터
        """
        try:
            # sensor_id에서 zone_id 추출 (예: 'sensor-IN-A01-1-load' -> 'IN-A01')
            parts = signal['sensor_id'].split('-')
            zone_id = f"{parts[1]}-{parts[2]}"
            
            if zone_id in self.zones_config:
                signal_type = signal['type'] # 'load', 'vibration'
                value = signal['value']
                self.zone_data_buffer[zone_id][signal_type].append(value)
        except (IndexError, KeyError) as e:
            print(f"Aggregator: Could not process invalid signal: {signal}. Error: {e}")

    def get_aggregated_data_and_clear_buffer(self) -> list:
        """
        버퍼에 저장된 데이터를 바탕으로 Zone별 집계 데이터를 생성하고 버퍼를 비웁니다.

        :return: 프론트엔드로 보낼 Zone 데이터 리스트
        """
        aggregated_zones = []
        
        for zone_id, zone_info in self.zones_config.items():
            buffer = self.zone_data_buffer[zone_id]
            
            # 버퍼에 데이터가 있는 경우 평균 계산, 없으면 0으로 처리
            avg_load = sum(buffer['load']) / len(buffer['load']) if buffer['load'] else 0
            avg_vib = sum(buffer['vibration']) / len(buffer['vibration']) if buffer['vibration'] else 0

            # 상태 결정
            if avg_load > 88:
                status = 'critical'
            elif avg_load > 70:
                status = 'warning'
            else:
                status = 'normal'

            # zone_data_schema.json 형식에 맞춤 (온도 제외)
            zone_data = {
                **zone_info,  # id, name, type 등 기본 정보
                "load": round(avg_load, 2),
                "vib": round(avg_vib, 3),
                "temp": 0, # 온도는 이제 사용하지 않으므로 0 또는 다른 기본값으로 설정
                "status": status,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            aggregated_zones.append(zone_data)
        
        # 처리가 끝난 버퍼 비우기
        self.zone_data_buffer.clear()
        
        return aggregated_zones
