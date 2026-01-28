# AzureRailLogistics Project Documentation

## 1. 프로젝트 개요
이 프로젝트는 물류 센터의 현황을 실시간으로 모니터링하고 분석하는 React 기반의 대시보드 애플리케이션입니다. 
전체적인 운영 현황을 파악하는 매크로(Macro) 뷰와 특정 구역의 세부 데이터를 분석하는 마이크로(Micro) 뷰로 구성되어 있습니다.

## 2. 파일 구조 (File Structure)
*   **Root**: `c:\Users\EL0100\Desktop\AzureRailLogistics\`
    *   **frontend\src\**
        *   `DashboardPage.jsx`: 전체 물류 센터의 KPI 및 구역별 상태를 모니터링하는 메인 대시보드 페이지입니다.
        *   `ZoneAnalyticsPage.jsx`: 특정 구역(Zone)의 상세 지표와 센서 데이터를 시각화하는 분석 페이지입니다.

## 3. 주요 기능 및 로직

### A. DashboardPage.jsx (Macro View)
*   **실시간 시뮬레이션**: `useEffect`와 `setInterval`을 사용하여 3초마다 각 구역의 부하(Load), 온도(Temp), 진동(Vib) 데이터를 랜덤하게 변동시키고, 이에 따른 상태(Normal, Warning, Critical)를 갱신합니다.
*   **재생(Playback) 모드**: 과거 데이터를 `history` 배열에 저장하고, 슬라이더를 조작하여 과거 특정 시점의 데이터를 조회할 수 있습니다.
*   **AI 인사이트**: 'ANALYZE' 버튼을 통해 가상의 AI 분석 로직을 실행하고 텍스트 인사이트를 제공합니다.
*   **네비게이션**: 구역 목록(`StatusTable`) 클릭 시 `useNavigate`를 통해 상세 페이지로 이동하며, 해당 구역의 `zoneId`와 `zoneName`을 State로 전달합니다.

### B. ZoneAnalyticsPage.jsx (Micro View)
*   **데이터 수신**: `useLocation` 훅을 사용하여 이전 페이지에서 전달받은 구역 정보를 표시합니다. (데이터 부재 시 기본값 사용)
*   **상세 지표**: TPH(시간당 처리량), 혼잡도, 재순환율, 에너지 효율 등 구체적인 운영 지표를 카드 형태로 표시합니다.
*   **시각화**:
    *   **Trend Chart**: SVG를 활용한 파동 형태의 데이터 트렌드 그래프.
    *   **Sensor Grid**: 랜덤하게 활성화되는 박스 그리드를 통해 센서 데이터 흐름을 시각적으로 표현.

## 4. 기술 스택
*   **Core**: React
*   **Styling**: styled-components
*   **Icons**: lucide-react
*   **Routing**: react-router-dom

## 5. 데이터 흐름 (Data Flow)
1.  **DashboardPage**에서 전체 구역 데이터(`config.zones`)를 관리 및 시뮬레이션합니다.
2.  사용자가 대시보드에서 특정 구역(예: 'PK-01')을 클릭합니다.
3.  **Router**가 화면을 `ZoneAnalyticsPage`로 전환하며, 선택된 구역의 ID와 이름을 전달합니다.
4.  **ZoneAnalyticsPage**는 전달받은 정보를 바탕으로 해당 구역에 특화된 상세 분석 화면을 렌더링합니다.

---

## 6. 센서 어댑터 시스템 (Sensor Adapter System)

### A. 개요
프로젝트는 어댑터 패턴을 사용하여 시뮬레이터와 실제 센서를 쉽게 전환할 수 있는 구조로 설계되었습니다.

### B. 어댑터 구조
```
sensor_adapter/
├── __init__.py          # 팩토리 함수 export
├── base.py              # SensorAdapter 추상 인터페이스
├── simulator_adapter.py # 시뮬레이터 어댑터 (개발/테스트용)
├── real_sensor_adapter.py # 실제 센서 어댑터 (프로덕션용)
└── factory.py           # 어댑터 생성 팩토리
```

### C. 어댑터 전환 방법

#### 1. 환경 변수를 통한 전환
```bash
# 시뮬레이터 모드 (기본값)
export SENSOR_ADAPTER=simulator
python backend/backend_main.py

# 실제 센서 모드
export SENSOR_ADAPTER=real_sensor
export SENSOR_GATEWAY_URL=http://your-sensor-gateway.com
export SENSOR_PROTOCOL=REST  # 또는 MQTT, MODBUS
export KAFKA_BROKER=localhost:9092
export SENSOR_POLL_INTERVAL=1
python backend/backend_main.py
```

#### 2. 코드를 통한 전환
```python
from sensor_adapter import create_adapter

# 시뮬레이터 사용
adapter = create_adapter("simulator", basket_pool, zones_config)

# 실제 센서 사용
adapter = create_adapter("real_sensor", sensor_config={
    "gateway_url": "http://sensor.company.com",
    "protocol": "REST",
    "kafka_broker": "localhost:9092",
    "polling_interval": 1
})
```

### D. 실제 센서 통합 가이드

#### 1. RealSensorAdapter 구현 완료 사항
`sensor_adapter/real_sensor_adapter.py` 파일에서 다음 메서드를 구현해야 합니다:

```python
def _connect_to_gateway(self):
    """센서 게이트웨이 연결 로직 구현"""
    # REST API 예시:
    # response = requests.get(f"{self.gateway_url}/status")
    # if response.status_code == 200:
    #     self.connected = True
    
    # MQTT 예시:
    # self.mqtt_client = mqtt.Client()
    # self.mqtt_client.connect(self.gateway_url, 1883)
    # self.mqtt_client.subscribe("sensor/basket/#")
    pass

def _poll_sensor_data(self):
    """센서 데이터 폴링 (REST/HTTP 기반)"""
    # REST API 예시:
    # response = requests.get(f"{self.gateway_url}/api/sensors/current")
    # data = response.json()
    # for sensor_event in data['sensors']:
    #     self._publish_to_kafka(sensor_event)
    pass

def _subscribe_sensor_events(self):
    """센서 이벤트 구독 (MQTT/WebSocket 기반)"""
    # MQTT 예시:
    # def on_message(client, userdata, message):
    #     sensor_data = json.loads(message.payload)
    #     self._publish_to_kafka(sensor_data)
    # 
    # self.mqtt_client.on_message = on_message
    # self.mqtt_client.loop_start()
    pass

def _convert_sensor_data_to_kafka_event(self, raw_data):
    """센서 데이터를 Kafka 이벤트 포맷으로 변환"""
    # 센서 데이터 포맷 예시:
    # raw_data = {
    #     "sensor_id": "SENSOR-01-001",
    #     "detected_basket": "BASKET-12345",
    #     "timestamp": "2026-01-26T10:30:00",
    #     "speed_mps": 0.5
    # }
    #
    # 변환 후:
    # kafka_event = {
    #     "sensor_id": raw_data["sensor_id"],
    #     "basket_id": raw_data["detected_basket"],
    #     "timestamp": raw_data["timestamp"],
    #     "speed": raw_data["speed_mps"],
    #     "event_type": "detection"
    # }
    # return kafka_event
    pass
```

#### 2. 센서 데이터 포맷 요구사항
실제 센서에서 다음 정보를 제공해야 합니다:

**필수 필드:**
- `sensor_id`: 센서 고유 ID (예: "01-PK-002-S001")
- `basket_id`: 감지된 바스켓 ID (예: "BASKET-00123")
- `timestamp`: 이벤트 발생 시각 (ISO 8601 형식)

**선택 필드:**
- `speed`: 바스켓 이동 속도 (m/s)
- `line_id`: 라인 ID
- `zone_id`: 존 ID
- `event_type`: 이벤트 유형 ("detection", "arrival", "departure")

#### 3. 통합 테스트 절차

1. **센서 게이트웨이 연결 테스트**
   ```bash
   curl http://your-sensor-gateway.com/api/status
   ```

2. **어댑터 시작**
   ```bash
   export SENSOR_ADAPTER=real_sensor
   export SENSOR_GATEWAY_URL=http://your-sensor-gateway.com
   python backend/backend_main.py
   ```

3. **상태 확인**
   ```bash
   curl http://localhost:8000/simulator/status
   # adapter_type이 "RealSensorAdapter"인지 확인
   ```

4. **이벤트 수신 확인**
   ```bash
   curl http://localhost:8000/baskets
   # motion_state, is_bottleneck 필드가 실시간으로 업데이트되는지 확인
   ```

#### 4. 프로덕션 배포 체크리스트

- [ ] 센서 게이트웨이 API 문서 확인
- [ ] 센서 데이터 포맷 매핑 완료
- [ ] `RealSensorAdapter` 메서드 구현
- [ ] 연결 재시도 로직 추가 (네트워크 장애 대응)
- [ ] 로깅 및 모니터링 설정
- [ ] Kafka 토픽 파티셔닝 최적화
- [ ] 환경 변수 설정 (`.env` 파일 또는 K8s ConfigMap)
- [ ] 부하 테스트 (센서 이벤트 처리량)
- [ ] 장애 복구 시나리오 테스트

### E. API 엔드포인트

#### 센서 어댑터 제어
- `GET /simulator/status` - 현재 어댑터 타입 및 상태 조회
- `POST /simulator/start` - 센서 어댑터 시작
- `POST /simulator/stop` - 센서 어댑터 중지
- `POST /simulator/reset` - 시뮬레이션 초기화 (시뮬레이터 모드만)

#### 어댑터 전환 시 변경 사항 없음
기존 REST API는 어댑터와 무관하게 동일하게 작동합니다:
- `GET /baskets` - 모든 바스켓 조회
- `GET /zones` - 모든 존 조회
- `POST /api/baskets/create` - 바스켓 생성