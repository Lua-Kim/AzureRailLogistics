# Azure Rail Logistics - 바스켓 센서 연동 구현 계획서

**작성일**: 2026-01-20  
**프로젝트 루트**: `c:\Users\EL0100\Desktop\AzureRailLogistics`

---

## 📋 목표

센서 이벤트와 바스켓 시뮬레이션을 연동하여:
- 바스켓이 라인 위에 올려지면 해당 센서들이 순차적으로 감지
- 바스켓이 라인을 통과하면서 센서 신호가 true → false로 변화
- 실제 물류 시스템의 바스켓 추적 시뮬레이션 구현

---

## 🏗️ 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                     프론트엔드 (React)                       │
│  [PIPELINE 시작/중지] [바스켓 생성 요청]                    │
└────────────────┬──────────────────────────┬─────────────────┘
                 │ API 호출                  │ API 호출
                 ▼                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   백엔드 (FastAPI)                           │
│  ✅ /simulator/start, /stop                                 │
│  ✅ /simulator/status                                       │
│  ❌ POST /api/baskets/create (필요)                         │
└──────────────────────────────────────────────────────────────┘
                 ▲              ▲                  ▲
         ┌───────┴──────┬───────┴────────┬────────┴────────┐
         │              │                │                │
    센서 생성      바스켓 관리      Movement 시뮬      Kafka
                                         │
┌──────────────────────────────────┐    │
│  센서_시뮬레이터 (독립 프로세스)  │    │
│  - sensor_data_generator.py ✅   │    │
│  - basket_movement.py ❌ (필요)  │◄───┘
│  - database.py ✅               │
└──────────────────────────────────┘
```

---

## 📊 현재 완성도

| 항목 | 상태 | 설명 |
|------|------|------|
| 센서 데이터 생성 | ✅ 완료 | 모든 센서의 상태 1초마다 생성 |
| ZONES DB 로드 | ✅ 완료 | DB에서 동적으로 존/라인 정보 로드 |
| 바스켓 풀 생성 | ✅ 완료 | 200개 바스켓 생성, 초기화 |
| 바스켓 API | ❌ 필요 | 프론트에서 바스켓 생성 요청 API |
| Movement 시뮬레이터 | ❌ 필요 | (여기가 비어있음) 바스켓 위치 추적 및 업데이트 |
| 센서-바스켓 연동 | ❌ 필요 | 바스켓 위치 기반 센서 신호 결정 |
| Kafka 토픽 확장 | ⚠️ 보류 | basket-events 토픽 추가 여부 |

---

## 🎯 핵심 개념 정의

### 1. 바스켓 생명주기

```
[available] (풀에서 대기)
    ↓
[in_transit] (라인에 올려짐 - assign_basket)
    ↓ (라인 길이 통과)
[arrived] (라인 끝에 도달 - 상태 종료)
```

### 2. 센서 신호 결정

**이전 (❌ 현재 - 확률 기반):**
```python
is_moving = random.random() < 0.6  # 60% 확률로 true
```

**이후 (✅ 변경 필요 - 바스켓 기반):**
```python
# 센서 위치에 바스켓이 있거나 지나가는가?
basket_at_sensor = check_basket_position(sensor_position, baskets)
signal = True if basket_at_sensor else False
```

### 3. 바스켓 이동 계산

```
라인 길이: 50m
바스켓 너비: 50cm (0.5m)
통과 시간: 계산 필요 (프론트엔드 매개변수)
  예: 50m ÷ 50초 = 1m/초

1초당 이동 거리 = 라인길이 / 통과시간
매초 위치 = 이전위치 + 이동거리
```

### 4. 센서 배치 규칙

```
라인 길이: 50m
센서 간격: 1m
센서 개수: 50개 (자동 계산)
센서 위치: 1m, 2m, 3m, ..., 50m

감지 범위 (바스켓 너비 50cm 기준):
  센서 위치 1m
  ├─ 0.75m ~ 1.25m 범위 감지
  └─ 바스켓 진입: true
  └─ 바스켓 완전 통과: false
```

---

## 📝 데이터베이스 스키마

### logistics_zones (기존)
```sql
CREATE TABLE logistics_zones (
    id INTEGER PRIMARY KEY,
    zone_id VARCHAR UNIQUE,      -- IB-01
    name VARCHAR,                 -- 입고
    lines INTEGER,                -- 라인 개수: 4
    length FLOAT,                 -- 라인 길이: 50m
    sensors INTEGER,              -- 총 센서 개수: 40
    created_at DATETIME,
    updated_at DATETIME
);
```

### logistics_lines (기존)
```sql
CREATE TABLE logistics_lines (
    id INTEGER PRIMARY KEY,
    zone_id VARCHAR FK,           -- IB-01
    line_id VARCHAR,              -- IB-01-001
    length FLOAT,                 -- 라인 길이: 50m
    sensors INTEGER,              -- 라인의 센서 개수: 10
    created_at DATETIME,
    updated_at DATETIME
);
```

### 센서 정보 (계산)
```
고정값으로 저장하지 않음
실시간 계산:
  - 센서 ID: SENSOR-{ZONE}{LINE}{NUMBER}
  - 센서 위치: 1m, 2m, ..., line.length
  - 센서 개수: line.length (1m 간격이므로)
```

---

## 🔄 Kafka 토픽 설계

### 1. sensor-events (기존)
**Topic**: `sensor-events`

**메시지 포맷**:
```json
{
  "zone_id": "IB-01",
  "line_id": "IB-01-001",
  "sensor_id": "SENSOR-IB0100001",
  "signal": true,           // ✅ 수정 필요: 랜덤 → 바스켓 기반
  "direction": "FORWARD",
  "speed": 50.0,
  "timestamp": "2026-01-20T10:00:00Z"
}
```

### 2. basket-events (신규 - 검토 필요)
**Topic**: `basket-events`

**메시지 포맷**:
```json
{
  "basket_id": "BASKET-00001",
  "zone_id": "IB-01",
  "line_id": "IB-01-001",
  "status": "in_transit",      // available, in_transit, arrived
  "position_meters": 15.5,     // 라인 내 현재 위치
  "destination": "OB-01",
  "timestamp": "2026-01-20T10:00:00Z"
}
```

**결정 필요**: 
- ❓ 이 토픽이 필요한가?
- ❓ 프론트엔드에서 사용할 정보인가?

---

## 📂 파일 구조 (예정)

```
c:\Users\EL0100\Desktop\AzureRailLogistics\
├── .env ✅
├── backend/
│   ├── database.py ✅
│   ├── models.py ✅
│   ├── backend_main.py ✅
│   ├── basket_routes.py ❌ (필요)
│   └── ...
├── sensor_simulator/
│   ├── database.py ✅
│   ├── sensor_data_generator.py ✅ (수정 필요)
│   ├── basket_movement.py ❌ (신규)
│   ├── sensor_event_schema.json ✅
│   └── ...
└── ...
```

---

## 🚀 구현 단계별 계획

### Phase 1: 바스켓 생성 API (백엔드)
**담당**: backend_main.py 또는 basket_routes.py

**목표**: 프론트엔드에서 바스켓 생성 요청 처리

**구현 내용**:
```python
# POST /api/baskets/create
@app.post("/api/baskets/create")
def create_baskets(
    zone_id: str,           # IB-01
    line_id: str,           # IB-01-001
    count: int,             # 생성할 바스켓 수
    destination: str = None # 목적지 (선택)
):
    # basket_pool에서 available 바스켓 가져오기
    # assign_basket() 호출로 할당
    # 응답: 할당된 바스켓 목록
```

**필요 정보**:
- ✅ basket_pool: 이미 초기화됨
- ✅ get_available_baskets(): 이미 구현됨
- ✅ assign_basket(): 이미 구현됨

**산출물**:
- `basket_routes.py` 또는 `backend_main.py` 내 엔드포인트

---

### Phase 2: Movement 시뮬레이터 (센서_시뮬레이터)
**담당**: sensor_simulator/basket_movement.py (신규)

**목표**: 1초마다 바스켓 위치 계산 및 업데이트

**구현 내용**:
```python
class BasketMovement:
    def __init__(self, basket_pool, zones):
        self.basket_pool = basket_pool
        self.zones = zones
        self.is_running = False
        self.thread = None
    
    def start(self):
        # 백그라운드 스레드 시작
    
    def _movement_worker(self):
        # 1초마다:
        # 1. in_transit 바스켓 조회
        # 2. 위치 계산
        # 3. 바스켓 업데이트
        # 4. 끝에 도달하면 status = arrived
    
    def stop(self):
        # 안전하게 중지
```

**핵심 로직**:
```python
# 위치 계산
통과시간 = 프론트엔드에서 받은 값 (기본값: 50초)
라인길이 = zone/line 정보에서 조회
이동거리_per_second = 라인길이 / 통과시간

매초:
    현재위치 += 이동거리_per_second
    if 현재위치 >= 라인길이:
        status = "arrived"
        update_basket_status()
```

**필요 정보**:
- ✅ basket_pool 인스턴스
- ✅ zones 정보
- ❓ 통과 시간 (프론트 매개변수 저장 필요?)

**산출물**:
- `sensor_simulator/basket_movement.py`

---

### Phase 3: 센서 신호 재설계 (센서_시뮬레이터)
**담당**: sensor_simulator/sensor_data_generator.py (수정)

**목표**: 바스켓 위치 기반으로 센서 신호 결정

**현재 코드** (❌ 제거):
```python
def generate_single_event(self, ...):
    is_moving = random.random() < signal_probability  # ❌ 랜덤
    signal = is_moving
```

**변경할 코드** (✅ 추가):
```python
def generate_single_event(self, zone_id, sensor_info, ...):
    # 센서 위치 계산
    sensor_position = sensor_info["position"]  # 1m, 2m, ...
    
    # 바스켓 위치 조회
    baskets_at_line = get_baskets_at_line(zone_id, line_id)
    
    # 이 센서 위치에 바스켓이 있는가?
    has_basket = any(
        basket_overlaps_sensor(basket, sensor_position)
        for basket in baskets_at_line
    )
    
    signal = has_basket
```

**필요 정보**:
- ✅ basket_pool 인스턴스
- ❓ 바스켓 위치 조회 메서드
- ❓ 바스켓-센서 겹침 판정 로직

**산출물**:
- `sensor_data_generator.py` 수정
- 새 메서드: `_check_basket_at_sensor()`

---

### Phase 4: 통합 및 테스트
**목표**: 전체 시스템 동작 확인

**테스트 시나리오**:
1. 센서 시뮬레이터 시작
2. 프론트에서 "바스켓 5개 생성" 요청
3. Movement 시뮬레이터가 위치 업데이트
4. 센서 신호가 바스켓을 따라 변화
5. 라인 끝 도달 시 바스켓 상태 변경

**검증 항목**:
- ✅ 센서 신호가 바스켓과 일치하는가?
- ✅ 바스켓 위치가 정확한가?
- ✅ 라인 끝 도달 감지?
- ✅ 여러 바스켓 동시 처리?

---

## 📌 진행 상황 기록

### 2026-01-20 초기 설계
- [x] 개념 정의 및 논의
- [x] 아키텍처 설계
- [x] 데이터베이스 스키마 확인
- [ ] Phase 1: 바스켓 생성 API
- [ ] Phase 2: Movement 시뮬레이터
- [ ] Phase 3: 센서 신호 재설계
- [ ] Phase 4: 통합 테스트

---

## 🔗 참고 파일

| 파일 | 위치 | 용도 |
|------|------|------|
| database.py | sensor_simulator/ | DB 연결, ZONES 로드 |
| basket_manager.py | sensor_simulator/ | 바스켓 풀 관리 |
| sensor_data_generator.py | sensor_simulator/ | 센서 이벤트 생성 |
| backend_main.py | backend/ | FastAPI 백엔드 |
| models.py | backend/ | 데이터 모델 |
| .env | 루트 | 환경 설정 |

---

## ⚠️ 주의사항

1. **센서 위치 정보**: 현재 DB에 없음
   - 계산식: 1m 간격 → 0m, 1m, 2m, ..., line_length
   - 런타임에 생성 필요

2. **동시성 관리**:
   - basket_pool 접근 시 lock 필요
   - Movement 시뮬레이터와 센서 제너레이터 동시 접근 주의

3. **통과 시간 파라미터**:
   - 현재 하드코딩: 50초
   - 프론트에서 설정 가능하게 변경 필요?

4. **Kafka 토픽**:
   - basket-events 필요 여부 미결정
   - 일단 진행하고 필요시 추가

---

## 📞 다음 단계

> **현재 상태**: 아키텍처 설계 완료, Phase 1 준비 단계  
> **다음 작업**: Phase 1 (바스켓 생성 API) 구현 승인 대기
