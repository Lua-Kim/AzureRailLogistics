# sensor_simulator/aggregator.py
import datetime
import time

class Aggregator:
    """
    개별 센서 이벤트를 수집하여 특정 시간 간격으로 집계된 데이터를 생성합니다.
    트래픽, 병목 현상 감지 및 통합 정보 제공에 중점을 둡니다.
    """
    def __init__(self, zones_config, aggregation_interval_seconds=5):
        self.zones_config = zones_config
        self.aggregation_interval_seconds = aggregation_interval_seconds
        self.sensor_buffers = {} # Stores raw events per sensor_id
        self.last_aggregated_time = time.time()

        # Initialize buffers for each potential sensor
        for zone in self.zones_config:
            for i in range(1, zone['lines'] + 1):
                sensor_id = f"{zone['id']}-S{i}"
                self.sensor_buffers[sensor_id] = []
        
        print(f"Aggregator initialized for {len(self.sensor_buffers)} sensors with {aggregation_interval_seconds}s interval.")

    def process_sensor_event(self, event):
        """단일 센서 이벤트를 버퍼에 추가합니다."""
        sensor_id = event['sensor_id']
        if sensor_id in self.sensor_buffers:
            self.sensor_buffers[sensor_id].append(event)
        # else: log an error or ignore unknown sensor

    def get_aggregated_data_and_clear_buffer(self):
        """
        현재 버퍼에 있는 이벤트를 집계하고, 집계된 데이터를 반환한 후 버퍼를 비웁니다.
        """
        aggregated_results = []
        current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

        for sensor_id, events in self.sensor_buffers.items():
            # Find corresponding zone info
            zone_id = sensor_id.split('-S')[0]
            zone_info = next((z for z in self.zones_config if z['id'] == zone_id), None)
            line_direction = zone_info['direction'] if zone_info else "UNKNOWN"

            if not events:
                # No events for this sensor in this interval, report default/zero values
                aggregated_results.append({
                    "aggregated_id": sensor_id,
                    "zone_id": zone_id,
                    "line_direction": line_direction,
                    "timestamp": current_time,
                    "aggregation_interval_sec": self.aggregation_interval_seconds,
                    "item_throughput": 0,
                    "avg_speed": 0.0,
                    "sensor_status_breakdown": {"정상": 0, "경고": 0, "오류": 0, "오프라인": 0},
                    "bottleneck_indicator": {
                        "is_congested": False,
                        "bottleneck_score": 0
                    }
                })
                continue

            # --- Aggregation Logic ---
            total_pass_events = 0
            total_speed = 0
            speed_count = 0
            status_breakdown = {"정상": 0, "경고": 0, "오류": 0, "오프라인": 0} # Initialize all statuses

            for event in events:
                if event['pass_event'] == 1:
                    total_pass_events += 1
                    total_speed += event['speed_at_sensor']
                    speed_count += 1
                status_breakdown[event['sensor_status']] = status_breakdown.get(event['sensor_status'], 0) + 1
            
            avg_speed = round(total_speed / speed_count, 2) if speed_count > 0 else 0.0

            # --- Bottleneck Indicator: Based purely on speed and throughput ---
            # 병목 현상 = 물류가 거의 정지 상태 (속도 저하)
            # 센서 상태는 별도의 유지보수 신호 (병목과 무관)
            is_congested = False
            bottleneck_score = 0
            
            # 유일한 병목 조건: 거의 정지 상태
            if avg_speed > 0 and avg_speed < 0.2:
                is_congested = True
                bottleneck_score = 0.9  # Critical bottleneck
            
            # 센서 상태 (오류/경고)는 병목이 아니라 유지보수 신호로만 사용

            aggregated_results.append({
                "aggregated_id": sensor_id,
                "zone_id": zone_id,
                "line_direction": line_direction,
                "timestamp": current_time,
                "aggregation_interval_sec": self.aggregation_interval_seconds,
                "item_throughput": total_pass_events,
                "avg_speed": avg_speed,
                "sensor_status_breakdown": status_breakdown,
                "bottleneck_indicator": {
                    "is_congested": is_congested,
                    "bottleneck_score": round(min(1.0, bottleneck_score), 2) # Ensure score is max 1.0
                }
            })
            self.sensor_buffers[sensor_id] = [] # Clear buffer for this sensor

        self.last_aggregated_time = time.time()
        return aggregated_results