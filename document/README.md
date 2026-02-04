# AzureRailLogistics - 물류센터 실시간 시뮬레이션 및 모니터링 시스템

## 📋 프로젝트 개요

**목적**: Azure 클라우드 기반의 물류센터 바스켓 운송 시뮬레이션 및 센서 데이터 수집 시스템

**구성**:
- 🎨 **Frontend**: React 기반 실시간 시각화
- 🔧 **Backend**: Python FastAPI 서버 (데이터 관리 및 API)
- 📡 **Sensor Simulator**: 물류센터 센서 데이터 생성 및 IoT Hub 전송
- ☁️ **Azure Infrastructure**: IoT Hub, EventHub, PostgreSQL

**현재 상태**: ✅ 운영 (2026-02-02 기준)

---

## 🏗️ 시스템 아키텍처

### 전체 흐름

```
센서 시뮬레이터          Azure 클라우드                    사용자
─────────────────────────────────────────────────────────────
센서 이벤트 생성   →  IoT Hub  →  IoT의 EventHub  →  Backend  →  Frontend
(port 5001)                                   (port 8000)  (port 3000)
                                                 ↓
                                          Azure PostgreSQL
```

### 주요 컴포넌트

| 컴포넌트 | 위치 | 포트 | 역할 |
|---------|------|------|------|
| **Backend** | VM | 8000 | API 서버, EventHub 소비, DB 관리 |
| **Sensor Simulator** | VM | 5001 | 센서 데이터 생성, IoT Hub 전송 |
| **Frontend** | 로컬/클라우드 | 3000 | 실시간 시각화, 제어 |
| **Azure IoT Hub** | 클라우드 | - | 센서 장치 연결, EventHub 게이트웨이 |
| **Azure EventHub** | 클라우드 | - | 이벤트 스트림 처리 |
| **PostgreSQL** | Azure | 5432 | Zone, Line, Sensor Event 저장 |

---

## 🚀 빠른 시작 (Quick Start)

### 전제조건
- Python 3.11+
- Node.js 16+
- Azure 구독 (LogisticsIoTHub, 이벤트 허브)
- .env 파일 설정 (예: `AZ_POSTGRE_DATABASE_URL`, `EVENTHUB_CONNECTION_STRING`)

```

---

## 📁 프로젝트 구조

```
AzureRailLogistics/
├── backend/                    # FastAPI 백엔드
│   ├── backend_main.py         # 메인 애플리케이션
│   ├── database.py             # PostgreSQL 연결 관리
│   ├── models.py               # SQLAlchemy 모델 (Zone, Line, Event)
│   ├── schemas.py              # Pydantic 스키마
│   ├── eventhub_consumer.py    # Azure EventHub 소비자
│   ├── basket_manager.py       # 바스켓 풀 관리
│   └── requirements.txt
│
├── sensor_simulator/           # 센서 데이터 생성
│   ├── api_server.py           # FastAPI 제어 서버
│   ├── sensor_data_generator.py # 센서 이벤트 생성
│   ├── basket_manager.py       # 바스켓 풀 동기화
│   ├── basket_movement.py      # 바스켓 이동 시뮬레이션
│   ├── database.py             # DB 쿼리 헬퍼
│   └── requirements.txt
│
├── frontend/                   # React 프론트엔드
│   ├── src/
│   │   ├── BasketVisualizationPage.jsx  # 메인 시각화 (바스켓 투입/이동/병목)
│   │   ├── App.js              # 라우터 설정
│   │   ├── api.js              # API 클라이언트
│   │   └── theme.js            # 테마/스타일
│   └── package.json
│
├── document/                   # 문서
│   ├── README.md               # 이 파일
│   ├── ARCHITECTURE_DESIGN_DECISIONS.md  # 아키텍처 결정사항
│   ├── AZURE_IOT_EDGE_SETUP.md # Azure 배포 가이드
│   └── ...
│
└── .env                        # 환경 변수 (git ignore)
```

---

## 🔌 API 명세

### Backend API (http://localhost:8000)

#### 기본 상태
```
GET /health
GET /health/db
GET /health/consumer
```

#### Zone & Line 설정
```
GET    /zones                          # 모든 존 조회
GET    /zones/config                   # 존 설정 상세 조회
POST   /zones/config                   # 새 존 생성
PUT    /zones/config/{zone_id}         # 존 업데이트
DELETE /zones/config/{zone_id}         # 존 삭제
POST   /zones/config/batch             # 여러 존 일괄 설정
```

#### 바스켓 관리
```
GET    /baskets                        # 모든 바스켓 조회
POST   /api/baskets/create             # 바스켓 생성
GET    /baskets/{basket_id}            # 특정 바스켓 조회
```

#### 센서 이벤트
```
GET    /api/sensor-events/db           # DB 저장된 센서 이벤트 조회
GET    /api/sensor-events/stats        # 센서 이벤트 통계
GET    /events/latest                  # 최근 이벤트
GET    /events/stats                   # 이벤트 통계
```

#### 병목 감지
```
GET    /bottlenecks                    # 병목 발생 존 및 바스켓 조회
```

#### 시뮬레이터 제어
```
GET    /simulator/status               # 시뮬레이터 상태
POST   /simulator/start                # 센서 시뮬레이터 시작
POST   /simulator/stop                 # 센서 시뮬레이터 정지
POST   /simulator/reset                # 시뮬레이터 초기화
```

### Sensor Simulator API (http://localhost:5001)

```
GET    /simulator/status               # 상태 조회
POST   /simulator/start                # 센서 생성 시작
POST   /simulator/stop                 # 센서 생성 중지
POST   /simulator/reset                # 재초기화 및 재시작
```

---

## 🎯 주요 기능

### 1. 실시간 바스켓 시각화
- **Zone별 Line 시각화**: 각 구역의 라인을 트랙으로 표시
- **바스켓 이동 추적**: 실시간 위치 업데이트 (100ms 주기)
- **병목 감지**: 정지된 바스켓 자동 감지 및 표시 (빨강)
- **센서 상태**: 각 라인의 센서 활성화 상태 표시

### 2. 바스켓 관리
- **순차 투입**: 대기열 기반 순차 투입 (충돌 방지)
- **라인 분산**: 혼잡도가 낮은 라인 우선 배분
- **자동 회수**: 도착한 바스켓 자동 회수
- **기본 개수**: 20개 바스켓

### 3. 센서 데이터 수집
- **IoT Hub 통합**: Azure IoT Hub를 통한 센서 데이터 수신
- **EventHub 처리**: 실시간 이벤트 스트림 처리
- **시간대 정렬**: KST (UTC+9) 기반 타임스탠프
- **배치 저장**: 8~10개 이벤트/초 PostgreSQL 저장

### 4. 디버그 및 모니터링
- **로깅**: 모든 API 호출, EventHub 수신, DB 저장 로깅
- **상태 확인**: 헬스체크 엔드포인트
- **통계**: 구역별 이벤트 통계

---

## ⚙️ 환경 설정

### .env 파일 예시

```bash
# Azure PostgreSQL
AZ_POSTGRE_DATABASE_URL=postgresql://logis_admin:!postgres16@psql-logistics-kr.postgres.database.azure.com:5432/logistics?sslmode=require

# Azure IoT Hub
IOT_HUB_DEVICE_CONNECTION_STRING=HostName=LogisticsIoTHub.azure-devices.net;DeviceId=logistics-edge-01;SharedAccessKey=...

# Azure EventHub (IoT Hub 호환)
EVENTHUB_CONNECTION_STRING=Endpoint=sb://iothub-ns-...servicebus.windows.net/;SharedAccessKeyName=owner;SharedAccessKey=...

# 프론트엔드
REACT_APP_API_URL=http://20.196.224.42:8000
```

---

## 🐳 Docker 배포

### 이미지 빌드

```bash
# 백엔드
docker build -t logistics-backend:latest ./backend

# 센서 시뮬레이터
docker build -t logistics-sensor-simulator:latest ./sensor_simulator
```

### 컨테이너 실행

```bash
# 백엔드
docker run -d \
  -p 8000:8000 \
  -e AZ_POSTGRE_DATABASE_URL=... \
  -e EVENTHUB_CONNECTION_STRING=... \
  --name logistics-backend \
  --network host \
  logistics-backend:latest

# 센서 시뮬레이터
docker run -d \
  -p 5001:5001 \
  -e IOT_HUB_DEVICE_CONNECTION_STRING=... \
  -e AZ_POSTGRE_DATABASE_URL=... \
  --name logistics-sensor-simulator \
  --network host \
  logistics-sensor-simulator:latest
```

---

## 📊 데이터베이스 스키마

### logistics_zones
```sql
CREATE TABLE logistics_zones (
  zone_id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  lines INT,              -- 라인 개수
  length FLOAT,          -- 총 길이 (m)
  sensors INT,           -- 센서 개수
  created_at TIMESTAMP
);
```

### logistics_lines
```sql
CREATE TABLE logistics_lines (
  zone_id VARCHAR,
  line_id VARCHAR,
  length FLOAT,          -- 라인 길이
  sensors INT,           -- 센서 개수
  PRIMARY KEY (zone_id, line_id)
);
```

### sensor_events
```sql
CREATE TABLE sensor_events (
  id SERIAL PRIMARY KEY,
  zone_id VARCHAR,
  line_id VARCHAR,
  sensor_id VARCHAR,
  basket_id VARCHAR,
  signal BOOLEAN,        -- 감지 여부
  speed FLOAT,          -- 속도 (m/s)
  created_at TIMESTAMP
);
```

---

## 🔄 데이터 흐름

### 1. 센서 → 클라우드
```
sensor_data_generator → IoT Hub → EventHub → Backend → PostgreSQL
(KST 타임스탠프)      (장치 수신)   (스트림)    (소비)     (저장)
```

### 2. 백엔드 → 프론트엔드
```
Frontend (GET /baskets)
    ↓
Backend (메모리 바스켓 풀 + DB)
    ↓
실시간 시각화
```

### 3. 프론트엔드 → 백엔드
```
사용자 작업 (바스켓 투입)
    ↓
POST /api/baskets/create
    ↓
Backend 바스켓 풀 업데이트 + DB 저장
    ↓
시뮬레이터 제어
```

---

## 🚨 주요 기능 및 로직

### 바스켓 투입 규칙 (deployment_queue_task)
1. 라인에 바스켓 없음 → 즉시 투입
2. 라인에 바스켓 있음 + 마지막 투입 후 0.8초 경과 → 투입 가능
3. 그 외 → 대기

### 바스켓 이동 (update_basket_positions_task)
1. 100ms마다 실행
2. 각 바스켓의 현재 위치에 해당하는 구간 속도 적용
3. 라인 끝 도달 시 'arrived' 상태로 전환
4. 앞 바스켓으로 인한 정지 감지 시 병목 플래그 설정

### 바스켓 회수 (recycle_baskets_task)
1. 5초마다 실행
2. 'arrived' 상태 바스켓 → 'available'로 전환
3. 재사용 가능 상태로 리셋

---

## 🔧 트러블슈팅

### EventHub 연결 실패
```
Error: "CBS Token authentication failed"
→ EVENTHUB_CONNECTION_STRING의 SharedAccessKey 확인
```

### 센서 데이터 미수신
```
확인사항:
1. 센서 시뮬레이터 실행 여부: GET http://localhost:5001/simulator/status
2. Backend 로그: "이벤트 수신: zone_id=..."
3. PostgreSQL 저장: SELECT COUNT(*) FROM sensor_events;
```

### 바스켓이 이동하지 않음
```
확인사항:
1. 백엔드 로그: "Basket Pool 초기화 완료" 확인
2. 바스켓 풀 상태: GET http://localhost:8000/baskets
3. 시뮬레이터 상태: GET http://localhost:8000/simulator/status
```

---

## 📝 로그 및 모니터링

### 주요 로그 메시지

**정상 작동:**
```
[센서 시뮬레이션] 메시지 스트리밍 스레드 시작됨
[EventHubConsumer] ✅ EventHub 연결 성공, 메시지 대기 중...
[EventHubConsumer] 이벤트 수신: zone_id=01-PK, signal=False, speed=0.0
✅ [HH:MM:SS] 8개 이벤트 DB 저장 완료
```

**오류 감지:**
```
❌ [HH:MM:SS] DB 저장 실패: ...
[EventHubConsumer] ❌ EventHub 연결 실패: ...
```

---

## 🤝 관련 문서

- [ARCHITECTURE_DESIGN_DECISIONS.md](ARCHITECTURE_DESIGN_DECISIONS.md) - 아키텍처 의사결정 및 멀티센터 확장 전략
- [AZURE_IOT_EDGE_SETUP.md](AZURE_IOT_EDGE_SETUP.md) - Azure 배포 가이드
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - 개선 로드맵

---

## 📅 버전 이력

**2026-02-02**: 현행 시스템 정리
- EventHub 통합 완료
- UI/UX 최적화 (Guide Panel, Statistics 콤팩트화, 병목 인라인 표시)
- 기본 투입 바스켓 20개로 변경
- 멀티센터 아키텍처 설계 문서 작성

---

## 📋 지난 로그 (Legacy)

> 이 섹션은 기존 아키텍처 및 레거시 컴포넌트에 대한 참고용 문서입니다.
> 2026-02-02 업데이트 이전의 구조를 담고 있습니다.

### 이전 구조 (2026-01-30 이전)

**페이지 구성 (사용 중단):**
- `DashboardPage.jsx` - 전체 물류 센터의 KPI 및 구역별 상태 (레거시)
- `ZoneAnalyticsPage.jsx` - 특정 구역 상세 분석 (레거시)

**센서 어댑터 시스템 (사용 중단):**
- Simulator vs Real Sensor 선택 구조
- REST API / MQTT / MODBUS 지원 (현재 불필요)

**메시징 시스템 (마이그레이션 완료):**
- 구 시스템: Kafka (로컬 메시징)
- 신 시스템: Azure EventHub (클라우드 기반)

### 마이그레이션 완료 항목

| 구성요소 | 구 방식 | 신 방식 | 상태 |
|---------|--------|--------|------|
| 센서 데이터 수집 | 로컬 센서 어댑터 | Azure IoT Hub | ✅ 완료 |
| 메시징 | Kafka | EventHub | ✅ 완료 |
| 데이터베이스 | SQLite | Azure PostgreSQL | ✅ 완료 |
| 시각화 | DashboardPage | BasketVisualizationPage | ✅ 완료 |

### 참고 자료

더 자세한 아키텍처 변경 이력은 [WORK_SUMMARY_2026-01-30.md](WORK_SUMMARY_2026-01-30.md)를 참조하세요.

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