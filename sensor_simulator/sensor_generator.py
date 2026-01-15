import random
import datetime

class SensorGenerator:
    """
    개별 센서에서 발생하는 원시 '신호' 데이터를 생성하는 클래스.
    이 클래스는 외부에서 ZONES_CONFIG와 TRAFFIC_PARAMETERS를 주입받아 사용합니다.
    """

    def __init__(self, zones_config, traffic_parameters):
        """
        SensorGenerator를 초기화합니다.

        :param zones_config: Zone 설정 정보가 담긴 리스트
        :param traffic_parameters: 물류량 변화에 영향을 미치는 외부 변수 딕셔너리
        """
        self.zones_config = zones_config
        self.traffic_parameters = traffic_parameters
        self.line_states = {}
        self._initialize_line_states()

    def _initialize_line_states(self):
        """각 라인의 초기 상태를 설정합니다."""
        for zone in self.zones_config:
            for i in range(1, zone['lines'] + 1):
                sensor_id = f"{zone['id']}-S{i}"
                self.line_states[sensor_id] = {
                    'last_pass_time': datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=random.randint(5, 10)),
                    'direction': zone.get('direction', 'UNKNOWN')
                }
        print("SensorGenerator: Initialized sensor states.")

    def _calculate_pass_probability(self):
        """교통 매개변수에 따라 pass_event 발생 확률을 계산합니다."""
        order = self.traffic_parameters['order_quantity']
        inbound = self.traffic_parameters['inbound_quantity']
        _return = self.traffic_parameters['return_quantity']
        workload = self.traffic_parameters['workload']

        # 간단한 선형 모델을 사용하여 확률 계산 (값을 0.1 ~ 0.9 범위로 정규화)
        # 기본 확률 (낮은 트래픽)
        base_prob = 0.1
        # 각 요소가 확률에 미치는 영향 (조정 가능)
        prob_from_order = order / 2000.0 * 0.2  # 주문량 2000이 최대 0.2의 확률 기여
        prob_from_inbound = inbound / 1500.0 * 0.15 # 입고량 1500이 최대 0.15의 확률 기여
        prob_from_return = _return / 200.0 * 0.05 # 반품량 200이 최대 0.05의 확률 기여
        prob_from_workload = workload / 100.0 * 0.3 # 작업 부하 100%가 최대 0.3의 확률 기여

        total_prob = base_prob + prob_from_order + prob_from_inbound + prob_from_return + prob_from_workload
        # 확률을 0.01에서 0.99 사이로 제한
        return max(0.01, min(0.99, total_prob))

    def _calculate_speed_range(self):
        """교통 매개변수에 따라 센서 통과 속도 범위를 계산합니다."""
        workload = self.traffic_parameters['workload']

        # 작업 부하가 높을수록 속도 범위가 줄어들고 최저 속도는 높아짐 (정체 시뮬레이션)
        min_speed = max(0.5, 0.5 + (workload / 100.0) * 1.5) # 워크로드 100% 시 최소 2.0 m/s
        max_speed = max(min_speed + 0.5, 5.0 - (workload / 100.0) * 2.0) # 워크로드 100% 시 최대 3.0 m/s

        return min_speed, max_speed

    def generate_sensor_data(self):
        """
        개별 레일 센서 데이터를 지속적으로 생성하는 제너레이터 함수입니다.
        새로운 스키마에 맞춰 pass_event, speed_at_sensor, sensor_status 등을 포함합니다.
        """
        while True:
            pass_probability = self._calculate_pass_probability()
            min_speed, max_speed = self._calculate_speed_range()

            for zone in self.zones_config:
                for i in range(1, zone['lines'] + 1):
                    sensor_id = f"{zone['id']}-S{i}"
                    current_time = datetime.datetime.now(datetime.timezone.utc)
                    sensor_state = self.line_states[sensor_id]

                    # 1. pass_event 시뮬레이션
                    # 최소 2초마다 한 번 통과 이벤트를 시뮬레이션합니다. (너무 자주 발생하지 않도록)
                    pass_event = 0
                    if (current_time - sensor_state['last_pass_time']).total_seconds() > 2 and random.random() < pass_probability:
                        pass_event = 1
                        sensor_state['last_pass_time'] = current_time

                    # 2. speed_at_sensor 시뮬레이션
                    speed_at_sensor = round(random.uniform(min_speed, max_speed), 2)

                    # 3. sensor_status 시뮬레이션 (대부분 정상)
                    status_choices = ["정상", "정상", "정상", "정상", "경고", "오류"]
                    # 작업 부하가 높을수록 경고/오류 확률 증가
                    status_weights = [80, 5, 2, 1, 10 + self.traffic_parameters['workload'] / 10, 3 + self.traffic_parameters['workload'] / 20]
                    sensor_status = random.choices(status_choices, weights=status_weights, k=1)[0]

                    yield {
                        "sensor_id": sensor_id,
                        "timestamp": current_time.isoformat(),
                        "pass_event": pass_event,
                        "line_direction": sensor_state['direction'],
                        "speed_at_sensor": speed_at_sensor,
                        "sensor_status": sensor_status
                    }

