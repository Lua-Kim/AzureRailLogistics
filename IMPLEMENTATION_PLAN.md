# 🛤️ Azure Rail Logistics - 통합 구현 계획서

**최종 업데이트**: 2026-01-26
**문서 버전**: 2.0

---

## 1. 📖 개요 (Overview)

이 문서는 Azure Rail Logistics 시스템의 기술적 구현 사항, 아키텍처, 데이터 흐름 및 핵심 컴포넌트의 역할을 상세히 기술합니다. 물류 센터 내 레일 위를 이동하는 바스켓의 움직임을 시뮬레이션하고, 센서 데이터를 생성하여 실시간으로 모니터링하는 시스템의 전체적인 구조와 동작 방식을 설명합니다.

본 문서는 프로젝트의 현재 구현 상태를 정확히 반영하는 것을 목표로 합니다.

---

## 2. 🏗️ 시스템 아키텍처 (System Architecture)

### 2.1. 아키텍처 다이어그램 (Architecture Diagram)

본 시스템은 **FastAPI 백엔드 서버가 핵심이 되어 시뮬레이션 스레드와 API 서비스를 모두 관장하는 중앙 집중형 아키텍처**를 채택하고 있습니다. 시뮬레이터는 별도의 외부 프로세스가 아닌, 백엔드 애플리케이션의 생명주기와 함께 관리되는 내부 스레드입니다.

```
+--------------------------------------------------------------------------+
|                        [ React Frontend (웹 브라우저) ]                    |
|  +--------------------------+  +---------------------------+  +---------+  |
|  | LogisticsRailSettingPage |  |  BasketVisualizationPage  |  | Debug.. |  |
|  | (레일/존 설정)           |  |  (실시간 시각화)          |  | (상태)  |  |
|  +--------------------------+  +---------------------------+  +---------+  |
+-------------------^----------------------------^----------------^---------+
                    | REST API 호출 (Axios)        | WebSocket/Polling |
                    v                            |                   |
+--------------------------------------------------------------------------+
|                        [ FastAPI Backend (서버) ]                          |
|                                                                          |
| +-------------------------+    +---------------------------------------+ |
| |   ▶ FastAPI Endpoints   |    |         ▶ Background Threads          | |
| |  -/zones (설정 CRUD)    |    |  +-----------------------------------+ | |
| |  -/baskets (조회/생성)  |    |  | BasketMovement (위치 계산 스레드) | | |
| |  -/simulator (제어)     |    |  +-----------------------------------+ | |
| |  -/events (센서 데이터) |    |  | SensorDataGenerator (Kafka 전송)  | | |
| +-------------------------+    |  +-----------------------------------+ | |
|             ^ ▲              |  | KafkaConsumer (이벤트 수신 스레드)| | |
|             | | Shared Memory|  +-----------------------------------+ | |
|             | +--------------+        |            ▲                 | |
|             |                |        |            |                 | |
|             |                |        v            |                 | |
| +-----------+---------------+  +------+-----------+-----------------+ |
| |   BasketPool (Thread-Safe)|  |  Logistics DB  |  [ Kafka Broker ] | |
| | (바스켓 객체 관리)        |  |  (SQLite)      |  - sensor-events  | |
| +---------------------------+  +----------------+  +-----------------+ |
+--------------------------------------------------------------------------+
```

### 2.2. 컴포넌트 설명 (Component Descriptions)

| 컴포넌트 | 주요 기술 | 역할 |
| :--- | :--- | :--- |
| **Backend** | FastAPI (Python) | API 서버, 시뮬레이션 스레드 관리, DB/Kafka 연동 등 시스템의 모든 비즈니스 로직을 총괄하는 컨트롤 타워입니다. |
| **Simulator Threads**| `threading` (Python) | 백엔드 프로세스 내에서 동작하는 백그라운드 스레드입니다. `BasketMovement`와 `SensorDataGenerator`가 각각 위치 계산과 센서 데이터 생성을 담당합니다. |
| **Frontend**| React (JavaScript) | 사용자 인터페이스(UI)를 제공합니다. 시스템 설정, 시뮬레이션 시각화, 디버깅 정보를 웹 브라우저에 렌더링합니다. |
| **Message Queue**| Apache Kafka | `SensorDataGenerator`가 생성한 센서 이벤트를 `sensor-events` 토픽으로 발행(Produce)하고, 백엔드의 `KafkaConsumer`가 이를 구독(Consume)합니다. |
| **Database** | SQLite | 물류 센터의 존(Zone), 라인(Line)과 같은 환경 설정 정보를 영구적으로 저장합니다. |

### 2.3. 기술 스택 (Technology Stack)

- **Backend**: Python 3.11+, FastAPI, Uvicorn, SQLAlchemy
- **Frontend**: React, Styled-Components, Axios
- **Message Queue**: Apache Kafka
- **Database**: SQLite
- **Concurrency**: Python `threading` 모듈

---

## 3. 🌊 데이터 흐름 (Data Flow)

### 3.1. 레일/존 환경 설정
1.  **[Frontend]** 사용자가 `LogisticsRailSettingPage`에서 존과 라인의 구성을 설정하고 '저장' 버튼을 클릭합니다.
2.  **[API]** `POST /zones/config/batch` API가 호출됩니다.
3.  **[Backend]** 수신된 구성 데이터로 **SQLite DB**의 `logistics_zones`와 `logistics_lines` 테이블을 전체 업데이트(overwrite)합니다.

### 3.2. 바스켓 생성 및 시뮬레이션
1.  **[Frontend]** 사용자가 `BasketVisualizationPage`에서 '바스켓 생성' 버튼을 클릭합니다.
2.  **[API]** `POST /api/baskets/create` API가 호출됩니다.
3.  **[Backend]**
    - `BasketPool`에서 가용 바스켓을 조회합니다.
    - **(Auto-Expansion)** 가용 바스켓이 부족할 경우, 풀의 크기를 동적으로 확장합니다.
    - 바스켓을 `in_transit` 상태로 변경하고, 요청된 시작 라인에 할당합니다.
4.  **[Simulator Threads]**
    - `BasketMovement` 스레드가 `in_transit` 상태의 바스켓을 감지하고, 1초마다 위치를 물리 법칙에 따라 계산 및 업데이트합니다.
    - `SensorDataGenerator` 스레드는 `BasketMovement`가 계산한 실시간 위치를 참조합니다.
    - 바스켓이 특정 센서의 감지 범위(`±0.5m`) 내에 들어오면, `signal: true` 이벤트를 생성하여 **Kafka** `sensor-events` 토픽으로 전송합니다.

### 3.3. 실시간 시각화 및 데이터 조회
1.  **[Backend]** `KafkaConsumer` 스레드가 `sensor-events` 토픽을 실시간으로 구독하고, 수신된 이벤트를 내부 메모리(`latest_events`)에 저장합니다.
2.  **[Frontend]** `BasketVisualizationPage`가 주기적으로 백엔드 API를 호출합니다.
    - `GET /baskets`: 모든 바스켓의 최신 상태와 `BasketMovement`가 계산한 실시간 위치(`position_meters`) 정보를 가져옵니다.
    - `GET /events/latest`: `KafkaConsumer`가 저장한 최근 센서 감지 이벤트를 가져옵니다.
3.  **[Frontend]** 수신된 데이터를 바탕으로 바스켓의 움직임을 렌더링하고, 활성화된 센서를 화면에 붉은 점으로 표시합니다.

### 3.4. 바스켓 회수 (재사용)
1.  **[Simulator Threads]** `BasketMovement`는 바스켓이 최종 목적지 라인 끝에 도달하면 상태를 `arrived`로 변경합니다.
2.  **[Backend]** `recycle_baskets_task` 비동기 백그라운드 작업이 주기적으로 `arrived` 상태의 바스켓을 탐색합니다.
3.  **[Backend]** 발견된 바스켓의 상태를 다시 `available`로 리셋하여 `BasketPool`에 반환함으로써 재사용 가능하게 만듭니다.

---

## 4. 🧩 핵심 컴포넌트 상세 (Component Details)

### 4.1. Backend Server (`backend/backend_main.py`)
- **역할**: 시스템의 메인 컨트롤러. FastAPI 애플리케이션의 생명주기(`startup`, `shutdown`)에 맞춰 모든 백그라운드 서비스(시뮬레이터, Kafka 컨슈머)를 관리합니다.
- **주요 로직**:
    - **`startup_event`**: 서버 시작 시 DB 초기화, `BasketPool`, `BasketMovement`, `SensorDataGenerator`, `KafkaConsumer`, `recycle_baskets_task`를 순차적으로 초기화하고 시작합니다. **모든 컴포넌트가 메모리를 공유**하며 유기적으로 동작하는 구조의 핵심입니다.
    - **`shutdown_event`**: 서버 종료 시 모든 백그라운드 스레드를 안전하게 중지시킵니다.
    - **REST API 제공**: 프론트엔드와 통신하며 시스템을 제어하고 데이터를 제공하는 모든 엔드포인트를 정의합니다.

### 4.2. Basket Pool (`sensor_simulator/basket_manager.py`)
- **역할**: 바스켓 객체의 생성, 할당, 상태 변경, 조회를 담당하는 메모리 내 객체 저장소입니다.
- **주요 특징**:
    - **Thread-Safe**: `threading.RLock`을 사용하여 여러 스레드(API 요청, Movement, Sensor)가 동시에 접근해도 데이터 정합성을 보장합니다.
    - **Auto-Expansion**: 바스켓 생성 요청 시 가용량이 부족하면 `expand_pool`을 통해 자동으로 풀 크기를 늘려 시스템 중단을 방지합니다.
    - **Lifecycle Management**: 바스켓의 상태를 `available` -> `in_transit` -> `arrived`로 관리합니다.

### 4.3. Movement Simulator (`sensor_simulator/basket_movement.py`)
- **역할**: `in_transit` 상태인 모든 바스켓의 물리적 움직임을 시뮬레이션합니다.
- **주요 로직**:
    - **위치 계산**: `_movement_worker` 루프가 1초마다 각 바스켓의 `이동 속도(거리/시간)`를 기반으로 새 위치를 계산하여 `basket_positions` 딕셔너리에 업데이트합니다.
    - **스마트 라우팅**: `_get_zone_sort_key` 메서드는 Zone ID의 명명 규칙(예: `01-IB`, `02-SR`)을 분석하여, **숫자 > IB/SR/OB 키워드 > 알파벳** 순으로 이동 경로를 자동으로 정렬합니다. 이를 통해 복잡한 설정 없이 물류 흐름 기반의 순차 이동이 가능합니다.
    - **자동 환승**: `_complete_basket_transit` 메서드는 바스켓이 라인 끝에 도달했을 때, 정렬된 다음 Zone을 찾아 해당 Zone의 라인 중 하나로 **무작위 배정**하여 부하를 분산시킵니다.

### 4.4. Sensor Simulator (`sensor_simulator/sensor_data_generator.py`)
- **역할**: `BasketMovement`의 실시간 위치 데이터를 기반으로 센서 감지 이벤트를 생성하고 Kafka로 전송합니다.
- **주요 로직**:
    - **위치 기반 감지**: `generate_zone_events` 메서드는 더 이상 랜덤 확률에 의존하지 않습니다. `BasketMovement`의 `basket_positions`를 직접 참조하여, 센서의 물리적 위치와 바스켓의 현재 위치가 **실제로 겹치는 경우에만** `signal: true` 이벤트를 생성합니다.
    - **성능 최적화**: 매번 모든 바스켓을 순회하는 대신, API 호출 시점의 바스켓 위치 정보를 미리 라인별로 그룹화하여 불필요한 반복 계산을 제거했습니다. (O(N*M) -> O(N+M))

### 4.5. Frontend (`frontend/src/`)
- **`LogisticsRailSettingPage.jsx`**: 사용자가 물류 센터의 전체 레이아웃(존, 라인 수, 길이 등)을 설정하고 서버에 저장하는 페이지입니다.
- **`BasketVisualizationPage.jsx`**: 시뮬레이션의 핵심 시각화 페이지. API로부터 받은 바스켓 위치와 센서 데이터를 사용해 실시간으로 바스켓의 움직임과 센서 활성 상태를 렌더링합니다.
- **`VisualizationDebugPage.jsx`**: 시스템의 내부 상태(바스켓 통계, 실시간 위치 로그, Kafka 이벤트 수신 현황)를 모니터링할 수 있는 개발자용 디버그 페이지입니다.

---

## 5. 📡 API 명세 (API Specification)

| Method | Endpoint | 상태 | 설명 |
| :--- | :--- | :---: | :--- |
| `POST` | `/zones/config/batch` | ✅ 완료 | 전체 존/라인 구성을 일괄적으로 업데이트(교체)합니다. |
| `GET` | `/zones` | ✅ 완료 | 현재 설정된 모든 존과 라인 정보를 조회합니다. |
| `POST`| `/api/baskets/create` | ✅ 완료 | 지정된 라인(또는 랜덤)에 새로운 바스켓을 생성하여 투입합니다. |
| `GET` | `/baskets` | ✅ 완료 | 모든 바스켓의 상태 및 실시간 위치 정보를 조회합니다. |
| `GET` | `/events/latest` | ✅ 완료 | Kafka에서 수신된 최근 센서 이벤트를 조회합니다. |
| `POST`| `/simulator/start` | ✅ 완료 | 시뮬레이터 스레드를 시작합니다. (서버 시작 시 자동 호출) |
| `POST`| `/simulator/stop` | ✅ 완료 | 시뮬레이터 스레드를 중지합니다. |
| `GET` | `/simulator/status` | ✅ 완료 | 시뮬레이터의 현재 실행 상태를 조회합니다. |

---

## 6. 🗃️ 데이터베이스 스키마 (Database Schema)

- **`logistics_zones`**: 물류 구획(Zone)의 마스터 정보 저장
    - `zone_id` (PK): 구획 고유 ID (예: "IB-01")
    - `name`: 구획 이름 (예: "입고 A")
    - `lines`: 보유 라인 수
    - `length`: 각 라인의 기본 길이 (m)
    - `sensors`: 구획 내 총 센서 수
- **`logistics_lines`**: 각 구획에 속한 개별 라인(Line) 정보 저장
    - `id` (PK)
    - `zone_id` (FK): 소속된 존의 ID
    - `line_id`: 라인 고유 ID (예: "IB-01-001")
    - `length`: 라인별 개별 길이 (m)
    - `sensors`: 라인별 센서 수

---

## 7. 🚀 실행 방법 (Setup & Run)

### 7.1. Prerequisites
- Python 3.9+
- Node.js 16+
- Docker (Kafka 실행용)

### 7.2. 실행 순서
1.  **Kafka 실행**:
    ```bash
    docker-compose up -d
    ```
2.  **Backend 실행**:
    ```bash
    # venv 활성화
    source venv/bin/activate 
    
    # 패키지 설치
    pip install -r backend/requirements.txt
    
    # 서버 실행
    uvicorn backend.backend_main:app --reload
    ```
3.  **Frontend 실행**:
    ```bash
    cd frontend
    
    # 패키지 설치
    npm install
    
    # 개발 서버 실행
    npm start
    ```
4.  **접속**: 웹 브라우저에서 `http://localhost:3000`으로 접속합니다.