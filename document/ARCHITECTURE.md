# Azure IoT Edge 기반 철도 물류 시스템 아키텍처

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [전체 아키텍처](#전체-아키텍처)
3. [컴포넌트 상세](#컴포넌트-상세)
4. [데이터 흐름](#데이터-흐름)
5. [배포 구조](#배포-구조)
6. [네트워크 구성](#네트워크-구성)
7. [API 명세](#api-명세)
8. [프로젝트 구조](#프로젝트-구조)

---

## 시스템 개요

### 목표
철도 물류센터의 바스켓 이동 상황을 실시간으로 모니터링하고 시각화하는 IoT Edge 기반 시스템.

### 주요 특징
- **Azure IoT Hub**: 중앙 메시지 브로커
- **Azure IoT Edge**: 로컬 컨테이너 런타임
- **Python 백엔드**: FastAPI 기반 API 서버
- **React 프론트엔드**: 실시간 대시보드 시각화
- **PostgreSQL**: 영속성 데이터 저장소

---

## 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Cloud (Azure Region)               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┐                                   │
│  │   Azure IoT Hub      │  (LogisticsIoTHub - S1 Tier)      │
│  │  - Device Registry   │                                   │
│  │  - Message Broker    │                                   │
│  │  - Event Hub         │                                   │
│  └──────────┬───────────┘                                   │
│             │                                               │
│             │ AMQP/MQTT (Bidirectional)                     │
│             │                                               │
└─────────────┼───────────────────────────────────────────────┘
              │
              │ Internet Connection
              │
┌─────────────┴─────────────────────────────────────────────────┐
│            Azure VM (Edge Runtime VM)                         │
│            IP: 20.196.224.42 (Ubuntu 24.04 LTS)              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         Azure IoT Edge Runtime (Docker Daemon)        │  │
│  │  edgeAgent (Container Orchestration)                  │  │
│  │  edgeHub (MQTT Broker & Router)                       │  │
│  ├─────────────┬──────────────┬──────────────┬───────────┤  │
│  │             │              │              │           │  │
│  │  ┌────────┐ │  ┌────────┐ │ ┌──────────┐ │ ┌────────┐│  │
│  │  │postgres│ │  │Backend │ │ │ Sensor   │ │ │ Kafka  ││  │
│  │  │:5432   │ │  │:8000   │ │ │Simulator │ │ │(future)││  │
│  │  │(Vol)   │ │  │(API)   │ │ │(Module)  │ │ │        ││  │
│  │  └────────┘ │  └────────┘ │ └──────────┘ │ └────────┘│  │
│  │             │              │              │           │  │
│  └─────────────┴──────────────┴──────────────┴───────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
              │
              │ HTTP (Port 8000)
              │
┌─────────────┴─────────────────────────────────────────────────┐
│         Local Development Machine (Windows)                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   React Development Server (localhost:3000)         │   │
│  │   ┌────────────────────────────────────────────┐    │   │
│  │   │  BasketVisualizationPage.jsx               │    │   │
│  │   │  - Zones 렌더링 (Map 기반)                 │    │   │
│  │   │  - Lines 표시 (Logistics Lines)            │    │   │
│  │   │  - Baskets 애니메이션 (Real-time)          │    │   │
│  │   └────────────────────────────────────────────┘    │   │
│  │   ┌────────────────────────────────────────────┐    │   │
│  │   │  api.js                                    │    │   │
│  │   │  - GET /zones                              │    │   │
│  │   │  - GET /baskets                            │    │   │
│  │   │  - GET /simulator/status                   │    │   │
│  │   │  - POST /simulator/start|stop|reset        │    │   │
│  │   └────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  .env: REACT_APP_API_URL=http://20.196.224.42:8000          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 컴포넌트 상세

### 1️⃣ Azure IoT Hub (Cloud)

**역할**: 중앙 메시지 브로커 및 디바이스 관리

**설정**:
- **SKU**: S1 (Standard) - 매월 400,000 메시지 포함
- **이름**: LogisticsIoTHub
- **지역**: Korea Central
- **리소스 그룹**: 2dt-final-team5

**주요 기능**:
- Device Registry: logistics-edge-01 등록
- Event Hub 호환 엔드포인트: 센서 이벤트 수신
- Twin Properties: 디바이스 상태 관리

**연결 문자열**:
```
HostName=LogisticsIoTHub.azure-devices.net;
SharedAccessKeyName=service;
```

---

### 2️⃣ Azure IoT Edge Runtime (VM)

**호스트 정보**:
- **IP**: 20.196.224.42
- **OS**: Ubuntu 24.04 LTS
- **사이즈**: Standard B2s
- **리소스 그룹**: 2dt-final-team5

**Edge Runtime 버전**:
- edgeAgent: 1.5
- edgeHub: 1.5
- Docker: 27.x

**배포 방식**: deployment.json (Azure Portal에서 관리)

#### 2.1 PostgreSQL 컨테이너

```yaml
이미지: postgres:15
포트: 5432 (호스트)
환경변수:
  - POSTGRES_DB: logistics
  - POSTGRES_USER: admin
  - POSTGRES_PASSWORD: admin123
볼륨: postgres-data:/var/lib/postgresql/data
상태: running (always restart)
```

**데이터베이스 스키마**:
```sql
-- logistics_zones 테이블
CREATE TABLE logistics_zones (
  id SERIAL PRIMARY KEY,
  zone_id VARCHAR(50) UNIQUE,
  zone_name VARCHAR(100),
  description TEXT,
  location_x FLOAT,
  location_y FLOAT,
  size_width FLOAT,
  size_height FLOAT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- logistics_lines 테이블
CREATE TABLE logistics_lines (
  id SERIAL PRIMARY KEY,
  line_id VARCHAR(50) UNIQUE,
  line_name VARCHAR(100),
  zone_id VARCHAR(50),
  start_point_x FLOAT,
  start_point_y FLOAT,
  end_point_x FLOAT,
  end_point_y FLOAT,
  length_meters FLOAT,
  speed_limit_kmh INT,
  priority INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (zone_id) REFERENCES logistics_zones(zone_id)
);

-- facility_presets 테이블 (물류센터 프리셋)
CREATE TABLE facility_presets (
  preset_key VARCHAR(50) PRIMARY KEY,
  preset_name VARCHAR(100) NOT NULL,
  description TEXT,
  total_zones INT NOT NULL,
  total_lines INT NOT NULL,
  total_length_m INT NOT NULL,
  total_sensors INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- preset_zones 테이블 (프리셋별 존 구성)
CREATE TABLE preset_zones (
  id SERIAL PRIMARY KEY,
  preset_key VARCHAR(50) REFERENCES facility_presets(preset_key) ON DELETE CASCADE,
  zone_id VARCHAR(50) NOT NULL,
  zone_name VARCHAR(100) NOT NULL,
  lines INT NOT NULL,
  length_m INT NOT NULL,
  sensors INT NOT NULL,
  zone_order INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_preset_zones_key ON preset_zones(preset_key);
```

**초기 데이터**: 
- **운영 데이터**: Zone 2개, Line 10개 (logistics_zones, logistics_lines)
- **프리셋 데이터**: 7개 물류센터 템플릿, 31개 존 구성 (facility_presets, preset_zones)
  - mfc (소형/도심 MFC): 40 라인, 500 센서
  - tc (통과형 센터): 40 라인, 1,500 센서
  - dc (광역 배송 센터): 260 라인, 5,100 센서
  - megaFc (메가 풀필먼트): 550 라인, 11,100 센서
  - superFc (초대형 풀필먼트): 1,050 라인, 16,300 센서
  - intlHub (국제 물류 허브): 580 라인, 9,500 센서
  - autoFc (자동화 물류센터): 800 라인, 9,500 센서

---

#### 2.2 Backend 컨테이너

```yaml
이미지: containerogis.azurecr.io/logistics-backend:latest
포트: 8000 (호스트)
기반: Python 3.11 + FastAPI + Uvicorn
환경변수:
  - DATABASE_URL: postgresql://admin:admin123@postgres:5432/logistics
  - IOT_HUB_CONNECTION_STRING: ${IOT_HUB_CONNECTION_STRING}
  - EVENTHUB_CONNECTION_STRING: ${EVENTHUB_CONNECTION_STRING}
  - EVENTHUB_CONSUMER_GROUP: $Default
상태: running (always restart, healthy)
```

**주요 클래스**:

**1. SensorEventConsumer** (eventhub_consumer.py)
```python
역할: Azure Event Hub에서 센서 이벤트 수신
스레드: 비동기 이벤트 루프 (daemon thread)
메모리: 최대 2,000개 이벤트 캐시
메서드:
  - start(): Consumer 시작
  - get_recent_events(limit): 최근 이벤트 조회
  - stop(): Consumer 중지
```

**2. BasketPool** (basket_manager.py)
```python
역할: 바스켓 상태 관리 (메모리 기반)
기능:
  - 바스켓 생성/삭제
  - 위치 업데이트
  - 상태 조회 (all, by_line, by_zone)
메서드:
  - create_basket(line_id): 새 바스켓 추가
  - update_basket_position(): 위치 업데이트
  - get_baskets_on_line(line_id): 특정 라인의 바스켓 조회
```

**3. FastAPI 애플리케이션** (backend_main.py)
```python
주요 엔드포인트:
  GET  /zones               → 모든 Zone 정보
  GET  /baskets             → 모든 Basket 정보
  GET  /simulator/status    → 센서 시뮬레이터 상태
  POST /simulator/start     → 센서 시뮬레이터 시작
  POST /simulator/stop      → 센서 시뮬레이터 중지
  POST /simulator/reset     → 센서 시뮬레이터 리셋
  GET  /events/latest       → 최근 이벤트
```

---

#### 2.3 Sensor Simulator 컨테이너 (IoT Edge Module)

```yaml
이미지: containerogis.azurecr.io/logistics-sensor-simulator:latest
타입: IoT Edge Module (ModuleClient 사용)
기반: Python 3.11
환경변수:
  - DATABASE_URL: postgresql://admin:admin123@postgres:5432/logistics
  - IOT_HUB_CONNECTION_STRING: ${IOT_HUB_CONNECTION_STRING}
상태: running (always restart)
```

**주요 클래스**:

**1. SensorDataGenerator** (sensor_data_generator.py)
```python
역할: 센서 데이터 생성 및 IoT Hub로 전송
클라이언트: IoTHubModuleClient (create_from_edge_environment)
메시지 프로토콜: AMQP (IoT Hub native)

생성 메커니즘:
  1. 데이터베이스에서 lines 정보 로드
  2. 각 line별로 basket 생성
  3. basket이 line을 따라 이동
  4. 이동 경로와 속도 기반 센서 메시지 생성
  5. IoT Hub로 메시지 전송

메시지 형식:
{
  "basket_id": "basket_001",
  "line_id": "01-PK-001",
  "position_x": 120.5,
  "speed_kmh": 15.2,
  "timestamp": "2026-01-29T12:34:56.789Z",
  "status": "in_transit"
}
```

**2. BasketMovement** (basket_movement.py)
```python
역할: 바스켓의 실시간 이동 시뮬레이션
기능:
  - Line을 따라 선형 이동
  - 속도 변동 (구간별 속도 제한)
  - 병목 지점 감지
메서드:
  - calculate_next_position(): 다음 위치 계산
  - get_current_speed(): 현재 속도 조회
  - is_bottleneck(): 병목 여부 확인
```

---

### 3️⃣ Frontend (React)

**기술 스택**:
- React 19.2.3
- Node.js (npm)
- Tailwind CSS (스타일링)
- Axios (HTTP Client)

**개발 서버**:
```bash
cd frontend
npm start
# localhost:3000에서 실행
```

**주요 파일**:

**1. BasketVisualizationPage.jsx**
```jsx
역할: 메인 시각화 페이지

기능:
  - Canvas 기반 Zone/Line 렌더링
  - Real-time Basket 위치 업데이트
  - 드래그 인터랙션 (Zone 이동)

렌더링 흐름:
  1. zones API에서 Zone 정보 로드
  2. baskets API에서 Basket 정보 로드
  3. 200ms마다 위치 업데이트
  4. Canvas에 렌더링 (SVG 등)

상태 관리:
  - zones: Zone 배열
  - baskets: Basket 배열
  - selectedZone: 선택된 Zone
  - isRunning: 센서 시뮬레이터 실행 상태
```

**2. api.js**
```javascript
역할: 백엔드 API 통신

주요 함수:
  - getZones(): GET /zones
  - getBaskets(): GET /baskets
  - getSimulatorStatus(): GET /simulator/status
  - startSimulator(): POST /simulator/start
  - stopSimulator(): POST /simulator/stop
  - resetSimulator(): POST /simulator/reset
  - getLatestEvents(): GET /events/latest

기본 URL: REACT_APP_API_URL 환경변수에서 로드
```

**3. .env (환경 설정)**
```
REACT_APP_API_URL=http://20.196.224.42:8000
```

---

## 데이터 흐름

### 전체 흐름도

```
센서 시뮬레이터               IoT Hub                  백엔드                 프론트엔드
      │                       │                         │                       │
      │ ① BasketMovement     │                         │                       │
      │   계산                │                         │                       │
      │                       │                         │                       │
      ├─→ ② 센서 메시지      │                         │                       │
      │    생성 (JSON)       │                         │                       │
      │                       │                         │                       │
      └─→ ③ ModuleClient    │                         │                       │
          .send_message()     │                         │                       │
                              │                         │                       │
                              ├─→ ④ Event Hub         │                       │
                              │    (Event Hubs SDK)    │                       │
                              │                         │                       │
                              │                         ├─→ ⑤ EventHubConsumer│
                              │                         │    .latest_events    │
                              │                         │    (캐시)            │
                              │                         │                       │
                              │                         ├─→ ⑥ /simulator/status
                              │                         │    endpoint           │
                              │                         │                       │
                              │                         │                       ├─→ ⑦ /zones API
                              │                         │                       │    (Canvas 렌더링)
                              │                         │                       │
                              │                         │                       ├─→ ⑧ /baskets API
                              │                         │                       │    (위치 표시)
                              │                         │                       │
                              │                         │                       ├─→ ⑨ 실시간 업데이트
                              │                         │                       │    (200ms)
```

### 1. 센서 데이터 생성 (Sensor Simulator)

```python
# sensor_data_generator.py
sensor_data = {
    'basket_id': 'basket_001',
    'line_id': '01-PK-001',
    'position_x': 100.5,
    'speed_kmh': 12.5,
    'timestamp': datetime.utcnow().isoformat() + 'Z',
    'status': 'in_transit'
}

# IoT Hub로 전송 (AMQP)
await self.iot_client.send_message_to_output(
    message=sensor_data,
    output_name="output1"
)
```

**전송 주기**: 500ms (설정 가능)
**메시지 크기**: ~200 bytes
**처리량**: 최대 1000 메시지/초

---

### 2. 메시지 라우팅 (IoT Edge Hub)

```json
// deployment.json의 routes
{
  "sensorToIoTHub": "FROM /messages/modules/logistics-sensor-simulator/outputs/* INTO $upstream"
}
```

**처리 과정**:
1. 센서 시뮬레이터 → edgeHub (MQTT 로컬)
2. edgeHub → Azure IoT Hub (AMQP over Internet)
3. IoT Hub Event Hub 엔드포인트에 저장

---

### 3. 이벤트 소비 (Backend)

```python
# eventhub_consumer.py
class SensorEventConsumer:
    async def _on_event(self, partition_context, event):
        event_data = json.loads(event.body_as_str())
        self.latest_events.append(event_data)
        
        # 최대 2000개만 메모리에 유지
        if len(self.latest_events) > self.max_events:
            self.latest_events.pop(0)
        
        await partition_context.update_checkpoint(event)
```

**이벤트 처리**:
- 메모리 기반 캐시 (DB 저장 미포함)
- 최대 2,000개 이벤트 유지
- 실시간 처리 (checkpoint 업데이트)

---

### 4. API 응답 (Backend)

```python
# /simulator/status endpoint
@app.get("/simulator/status")
async def get_simulator_status():
    return {
        "running": sensor_simulator.is_running,
        "events_received": len(consumer.latest_events),
        "latest_event_time": None,  # 선택사항
        "adapter_type": "SimulatorAdapter",
        "line_speed_zones": {...}  # 10개 line의 속도 정보
    }
```

---

### 5. 프론트엔드 렌더링 (React)

```jsx
// BasketVisualizationPage.jsx
useEffect(() => {
  const interval = setInterval(async () => {
    const baskets = await getBaskets();
    setBaskets(baskets);
    
    // Canvas에 렌더링
    drawZones(zones);
    drawLines(zones);
    drawBaskets(baskets);
  }, 200);  // 200ms마다 업데이트
  
  return () => clearInterval(interval);
}, []);
```

**렌더링 성능**:
- 프레임 레이트: 5 FPS (200ms 주기)
- 렌더 시간: < 50ms
- 네트워크 레이턴시: < 100ms (로컬 테스트)

---

## 배포 구조

### 배포 파일 (deployment.json)

```json
{
  "modulesContent": {
    "$edgeAgent": {
      "properties.desired": {
        // 레지스트리 자격증명
        "registryCredentials": {
          "containerogis": {
            "username": "containerogis",
            "password": "${REGISTRY_PASSWORD}",
            "address": "containerogis.azurecr.io"
          }
        },
        // 시스템 모듈
        "systemModules": {
          "edgeAgent": {...},
          "edgeHub": {...}
        },
        // 커스텀 모듈
        "modules": {
          "postgres": {...},
          "logistics-backend": {...},
          "logistics-sensor-simulator": {...}
        }
      }
    },
    "$edgeHub": {
      "properties.desired": {
        // 메시지 라우팅
        "routes": {
          "sensorToIoTHub": "FROM /messages/modules/logistics-sensor-simulator/outputs/* INTO $upstream"
        }
      }
    }
  }
}
```

### 배포 프로세스

```
로컬 deployment.json (VS Code)
        ↓
클라우드 유효성 검사
        ↓
Azure IoT Hub Device Twin 업데이트
        ↓
edgeAgent가 manifests 감지
        ↓
필요한 Docker 이미지 풀링 (ACR에서)
        ↓
컨테이너 시작
        ↓
헬스 체크
        ↓
배포 완료 (status: "Up ... (healthy)")
```

### 배포 시간

| 단계 | 시간 |
|------|------|
| 유효성 검사 | 5초 |
| Twin 업데이트 | 10초 |
| 이미지 풀링 (처음) | 60초 |
| 이미지 풀링 (캐시됨) | 5초 |
| 컨테이너 시작 | 15초 |
| 헬스 체크 | 58초 |
| **총계 (처음)** | **150초** |
| **총계 (캐시)** | **93초** |

---

## 네트워크 구성

### Azure NSG (Network Security Group) 규칙

```
Rule Name           | Priority | Direction | Access | Protocol | Port | Source | Destination
─────────────────────────────────────────────────────────────────────────────────────────
AllowBackendAPI     | 100      | Inbound   | Allow  | TCP      | 8000 | *      | *
AllowPostgreSQL     | 110      | Inbound   | Allow  | TCP      | 5432 | *      | *
DenyAllInbound      | 65500    | Inbound   | Deny   | *        | *    | *      | *
AllowAllOutbound    | 65500    | Outbound  | Allow  | *        | *    | *      | *
```

### 통신 포트

```
클라이언트 (로컬)          Azure VM (20.196.224.42)
     │                            │
     ├─ HTTP:3000 ─────────────→ (개발 서버)
     │
     ├─ HTTP:8000 ──────────────→ Backend API (FastAPI)
     │                            │
     │                            ├─ PostgreSQL:5432 (내부)
     │                            │
     │                            ├─ AMQP (IoT Hub 통신)
     │                            │
     │                            └─ edgeHub (MQTT)
     │
     └─ Internet ────────────────→ Azure IoT Hub (포트 5671, 8883, 443)
```

### 연결 문자열 (암호화)

```
# IoT Device (Edge Device)
HostName=LogisticsIoTHub.azure-devices.net;
DeviceId=logistics-edge-01;

# Event Hub Consumer (Service)
HostName=LogisticsIoTHub.azure-devices.net;
SharedAccessKeyName=service;

# Container Registry
Server: containerogis.azurecr.io
Username: containerogis
```

---

## API 명세

### Zones API

**엔드포인트**: `GET /zones`

**응답 형식**:
```json
{
  "zones": [
    {
      "id": 1,
      "zone_id": "01-PK",
      "zone_name": "포장존",
      "description": "패키징 및 포장 존",
      "location": {
        "x": 100,
        "y": 150
      },
      "size": {
        "width": 200,
        "height": 150
      },
      "lines": [
        {
          "id": 1,
          "line_id": "01-PK-001",
          "line_name": "라인 1",
          "start_point": {"x": 100, "y": 150},
          "end_point": {"x": 300, "y": 150},
          "length_meters": 200,
          "speed_limit_kmh": 20,
          "line_speed_zones": [...]
        },
        ...
      ]
    },
    ...
  ]
}
```

**응답 시간**: < 50ms (데이터베이스 캐시됨)

---

### Baskets API

**엔드포인트**: `GET /baskets`

**응답 형식**:
```json
{
  "baskets": [
    {
      "basket_id": "basket_001",
      "line_id": "01-PK-001",
      "position": {
        "x": 150.5,
        "y": 150.0
      },
      "speed_kmh": 15.2,
      "status": "in_transit",
      "created_at": "2026-01-29T12:34:56.789Z",
      "updated_at": "2026-01-29T12:35:12.345Z"
    },
    ...
  ],
  "total_count": 50
}
```

**응답 시간**: < 100ms (메모리 기반)

---

### Simulator Control APIs

**시작**: `POST /simulator/start`
```json
{
  "status": "started",
  "message": "센서 시뮬레이터 시작됨"
}
```

**중지**: `POST /simulator/stop`
```json
{
  "status": "stopped",
  "message": "센서 시뮬레이터 중지됨"
}
```

**리셋**: `POST /simulator/reset`
```json
{
  "status": "reset",
  "message": "센서 시뮬레이터 초기화됨",
  "baskets_cleared": 50
}
```

**상태 조회**: `GET /simulator/status`
```json
{
  "running": true,
  "events_received": 1250,
  "latest_event_time": "2026-01-29T12:35:12.789Z",
  "adapter_type": "SimulatorAdapter",
  "line_speed_zones": {
    "01-PK-001": [
      {"segment": 0, "start_x": 100, "end_x": 120, "speed_kmh": 20},
      {"segment": 1, "start_x": 120, "end_x": 200, "speed_kmh": 15},
      {"segment": 2, "start_x": 200, "end_x": 300, "speed_kmh": 10}
    ],
    ...
  }
}
```

---

### Preset Management APIs

**프리셋 목록 조회**: `GET /presets`
```json
{
  "presets": [
    {
      "preset_key": "superFc",
      "preset_name": "초대형 풀필먼트 (Super FC)",
      "description": "최대 규모 FC, 반품 처리까지 포함한 초대형 시설",
      "total_zones": 8,
      "total_lines": 1050,
      "total_length_m": 16300,
      "total_sensors": 16300
    },
    {
      "preset_key": "megaFc",
      "preset_name": "메가 풀필먼트 (FC)",
      "description": "이커머스 전용, 검수/가공/분류까지 포함한 대형 FC",
      "total_zones": 7,
      "total_lines": 550,
      "total_length_m": 11100,
      "total_sensors": 11100
    },
    ...
  ]
}
```

**프리셋 상세 조회**: `GET /presets/{preset_key}`
```json
{
  "preset_key": "megaFc",
  "preset_name": "메가 풀필먼트 (FC)",
  "zones": [
    {
      "zone_id": "01-IB",
      "zone_name": "입고",
      "lines": 40,
      "length": 800,
      "sensors": 800,
      "zone_order": 1
    },
    {
      "zone_id": "02-IS",
      "zone_name": "검수",
      "lines": 40,
      "length": 600,
      "sensors": 600,
      "zone_order": 2
    },
    ...
  ]
}
```

**프리셋 적용**: `POST /presets/{preset_key}/apply`
```json
{
  "status": "success",
  "message": "프리셋 'megaFc'가 성공적으로 적용되었습니다.",
  "preset_key": "megaFc",
  "zones_created": 7,
  "lines_created": 550,
  "sensors_created": 11100,
  "simulator_restarted": true
}
```

**참고**: 프리셋 적용 시 기존의 모든 zones/lines 데이터가 삭제되고 프리셋 데이터로 교체됩니다.

---

## 프로젝트 구조

```
AzureRailLogistics/
├── backend/
│   ├── backend_main.py              # FastAPI 애플리케이션
│   ├── eventhub_consumer.py         # Event Hub 수신
│   ├── basket_manager.py            # Basket 상태 관리
│   ├── database.py                  # DB 연결
│   ├── models.py                    # SQLAlchemy ORM 모델
│   ├── schemas.py                   # Pydantic 스키마
│   ├── requirements.txt             # Python 의존성
│   ├── Dockerfile                   # 백엔드 컨테이너 빌드
│   └── __pycache__/
│
├── frontend/
│   ├── src/
│   │   ├── App.js                   # 메인 애플리케이션
│   │   ├── api.js                   # API 통신
│   │   ├── BasketVisualizationPage.jsx  # 메인 시각화
│   │   ├── GlobalStyle.js           # 전역 스타일
│   │   └── index.js                 # 진입점
│   ├── public/
│   │   ├── index.html
│   │   └── manifest.json
│   ├── .env                         # 환경 설정
│   ├── package.json
│   ├── tailwind.config.js
│   └── node_modules/
│
├── sensor_simulator/
│   ├── sensor_data_generator.py     # 센서 데이터 생성
│   ├── basket_movement.py           # Basket 이동 로직
│   ├── database.py                  # DB 연결
│   ├── requirements.txt
│   ├── Dockerfile
│   └── __pycache__/
│
├── sensor_adapter/
│   ├── base.py                      # 기본 어댑터 클래스
│   ├── factory.py                   # 어댑터 팩토리
│   ├── simulator_adapter.py         # 시뮬레이터 구현
│   └── real_sensor_adapter.py       # 실센서 구현 (미사용)
│
├── Data_schema/
│   ├── logistics_basket_schema.json
│   ├── logistics_center_schema.json
│   ├── logistics_line_schema.json
│   └── logistics_sensor_schema.json
│
├── document/
│   ├── ARCHITECTURE.md              # 시스템 아키텍처 문서
│   ├── IMPROVEMENTS.md              # 개선 제안 사항
│   ├── PRESET_API_GUIDE.md          # 프리셋 API 가이드
│   ├── AZURE_IOT_EDGE_SETUP.md      # Azure IoT Edge 설정 가이드
│   └── 물류유통센터 배경정보.md      # 물류센터 프리셋 스펙
│
├── init_presets_sqlalchemy.py       # 프리셋 DB 초기화 스크립트
├── init_presets.sql                 # 프리셋 SQL 스크립트
├── deployment.json                  # IoT Edge 배포 매니페스트 (gitignore)
├── deployment.template.json         # 배포 템플릿
├── docker-compose.yml               # 로컬 개발용
├── .env                             # 환경변수 (gitignore)
├── .gitignore
├── README.md
├── IMPLEMENTATION_PLAN.md           # 구현 계획
└── package.json
```

---

## 주요 기술 스택

| 계층 | 기술 | 버전 |
|------|------|------|
| **클라우드** | Azure IoT Hub | S1 |
| **에지** | Azure IoT Edge Runtime | 1.5 |
| **컨테이너** | Docker | 27.x |
| **백엔드** | Python | 3.11 |
| **프레임워크** | FastAPI | 0.104+ |
| **웹 서버** | Uvicorn | 0.24+ |
| **데이터베이스** | PostgreSQL | 15 |
| **메시지** | AMQP (IoT Hub) | - |
| **프론트엔드** | React | 19.2.3 |
| **스타일** | Tailwind CSS | 3.x |
| **빌드** | npm | 10.x |

---

## 배포 체크리스트

```
[ ] Azure 리소스 생성
    [ ] IoT Hub (LogisticsIoTHub, S1)
    [ ] Container Registry (containerogis)
    [ ] Virtual Machine (edge-runtime-vm)
    [ ] 리소스 그룹 (2dt-final-team5)

[ ] IoT Edge 환경 설정
    [ ] VM에 IoT Edge Runtime 설치
    [ ] Edge Device 등록 (logistics-edge-01)
    [ ] deployment.json 작성

[ ] Docker 이미지 빌드 및 푸시
    [ ] Backend 이미지 빌드
    [ ] Sensor Simulator 이미지 빌드
    [ ] 이미지를 ACR에 푸시

[ ] 데이터베이스 초기화
    [ ] PostgreSQL 테이블 생성
    [ ] 초기 데이터 삽입 (zones, lines)

[ ] 네트워크 설정
    [ ] NSG 규칙 추가 (포트 8000, 5432)
    [ ] VM에서 API 접근 확인

[ ] 프론트엔드 배포
    [ ] .env 파일 작성 (API URL)
    [ ] npm install
    [ ] npm start 또는 npm run build

[ ] 검증
    [ ] GET /zones 응답 확인
    [ ] GET /baskets 응답 확인
    [ ] 센서 시뮬레이터 시작 확인
    [ ] 프론트엔드에서 실시간 시각화 확인
```

---

## 문제 해결

### 센서 시뮬레이터가 연결되지 않음

**원인**: DeviceClient 대신 ModuleClient 사용
**해결**: `sensor_data_generator.py`에서 `IoTHubModuleClient.create_from_edge_environment()` 사용

```python
# ❌ 잘못됨
from azure.iot.device import IoTHubDeviceClient
client = IoTHubDeviceClient.create_from_connection_string(connection_string)

# ✅ 올바름
from azure.iot.device import IoTHubModuleClient
client = IoTHubModuleClient.create_from_edge_environment()
```

---

### 백엔드 API 500 에러

**원인**: `consumer.get_event_count()` 메서드 없음
**해결**: `len(consumer.latest_events)` 직접 계산

```python
# ❌ 잘못됨
events_count = consumer.get_event_count()

# ✅ 올바름
events_count = len(consumer.latest_events)
```

---

### 프론트엔드가 백엔드에 연결할 수 없음

**원인**: localhost:8000 대신 클라우드 IP 필요
**해결**: `.env` 파일에 REACT_APP_API_URL 설정

```bash
# .env
REACT_APP_API_URL=http://20.196.224.42:8000
```

---

## 모니터링 및 로깅

### 로그 확인

```bash
# 백엔드 로그
docker logs logistics-backend -f

# 센서 시뮬레이터 로그
docker logs logistics-sensor-simulator -f

# PostgreSQL 로그
docker logs postgres -f
```

### 헬스 체크

```bash
# 백엔드 상태
curl http://20.196.224.42:8000/zones

# PostgreSQL 연결
psql -h 20.196.224.42 -U admin -d logistics -c "SELECT COUNT(*) FROM logistics_zones;"

# IoT Edge 모듈 상태
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## 향후 개선 사항

1. **데이터베이스 영속성**
   - Event Hub 메시지 DB 저장
   - 시계열 데이터 통합

2. **고급 분석**
   - 병목 지점 자동 감지
   - 처리량 예측

3. **모니터링**
   - Azure Monitor 통합
   - 실시간 경고

4. **스케일링**
   - 다중 IoT Edge 디바이스 지원
   - 마이크로서비스 아키텍처

5. **프로덕션 준비**
   - 컨테이너화된 프론트엔드 배포
   - SSL/TLS 통신 암호화
   - 사용자 인증 (Azure AD)

---

**최종 업데이트**: 2026년 1월 29일
**시스템 상태**: ✅ 완전히 작동 중
