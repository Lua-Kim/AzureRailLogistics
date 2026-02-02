# Azure Rail Logistics - 작업 요약 (2026-02-02)

## 📋 오늘의 주요 작업

### 1. position_y 제거 및 정리
**배경:**
- SensorEvent 모델에서 position_x, position_y 컬럼 존재
- position_y는 사용되지 않아 제거 결정

**수정 파일:**
- `backend/models.py` - SensorEvent.position_y 컬럼 삭제
- `backend/eventhub_consumer.py` - position_y 할당 로직 제거
- `backend/backend_main.py` - API 응답에서 position_y 필드 제거
- `document/IMPROVEMENTS.md` - 예제 코드 정리

**결과:**
✅ 데이터 모델 단순화, 불필요한 필드 제거

---

### 2. 센서 이벤트에 basket_id, position_x 추가

**배경:**
- 현재: 센서가 이벤트를 생성할 때 바스켓 ID 정보를 버리고 있었음
- 문제: DB에 저장되는 센서 이벤트에 "어떤 바스켓이 감지되었는지" 정보가 없음

**설계 결정: 옵션 1 (센서가 basket_id 포함)**
```
센서가 이미 바스켓 위치를 알고 있음
  └─ 감지 시점에 basket_id 함께 전송
     └─ DB에 저장
```

**수정 파일:**
`sensor_simulator/sensor_data_generator.py` (3곳 수정)

1. **287-300줄**: baskets_in_zone 구조 변경
   - Before: `{line_id: [pos_meters, ...]}`
   - After: `{line_id: [(basket_id, pos_meters), ...]}`

2. **320-328줄**: 센서 감지 시 basket_id 추출
   - detected_basket_id 변수 추가
   - 루프에서 basket_id, b_pos 언팩

3. **350-357줄**: event에 필드 추가
   ```python
   event = {
       "zone_id": zone_id,
       "line_id": line_id,
       "sensor_id": sensor_id,
       "basket_id": detected_basket_id,  # ✅ 새로 추가
       "signal": signal,
       "timestamp": timestamp,
       "speed": 50.0 * speed_modifier if signal else 0.0,
       "position_x": sensor_pos  # ✅ 새로 추가
   }
   ```

**DB 저장 흐름:**
```
센서 이벤트 생성 (signal=true/false, basket_id=BASKET-XXX, position_x=10.5m)
  ↓
IoT Hub 전송 (1초마다)
  ↓
EventHub Consumer 수신 (거의 실시간)
  ↓
배치 버퍼 (10개 모으거나 1초 대기)
  ↓
DB 저장 (sensor_events 테이블)
```

**저장되는 데이터 예시:**
```json
{
  "timestamp": "2026-02-02T12:34:56.123456",
  "zone_id": "01-PK",
  "basket_id": "BASKET-00001",
  "sensor_id": "01-PK-001-S001",
  "signal": true,
  "speed": 50.0,
  "position_x": 10.5
}
```

---

### 3. Docker 이미지 빌드 및 배포

**문제:**
- Dockerfile이 상대 경로를 잘못 참조
- `COPY backend/requirements.txt` → 빌드 컨텍스트 오류

**수정:**
`backend/Dockerfile` - 경로 정정
```dockerfile
# Before
COPY backend/requirements.txt .
COPY backend/ .
COPY sensor_simulator /app/sensor_simulator

# After
COPY requirements.txt .
COPY . .
```

**배포 프로세스:**
```powershell
.\deploy-to-vm.ps1
```

**배포 스크립트 생성** (`deploy-to-vm.ps1`)
- 자동화 5단계:
  1. Backend 이미지 빌드
  2. Sensor Simulator 이미지 빌드
  3. ACR에 이미지 푸시 (2개)
  4. VM에서 새 이미지 다운로드
  5. 모듈 재시작

**결과:**
✅ Backend: digest sha256:5fb58848...
✅ Sensor Simulator: digest sha256:e42357bc...
✅ VM 모듈: logistics-backend, logistics-sensor-simulator 재시작 (15초 전)

---

### 4. EventHub Consumer 수정

**SQLAlchemy 2.0 호환성 문제:**
```python
# Before (오류)
count = db.execute('SELECT COUNT(*) FROM sensor_events').scalar()

# After (수정)
from sqlalchemy import text
count = db.execute(text('SELECT COUNT(*) FROM sensor_events')).scalar()
```

**수정 파일:**
`backend/eventhub_consumer.py` (193-197줄)

---

## 🏗️ 아키텍처 논의: Dead Letter Queue 도입

### 현재 아키텍처의 문제점
```
IoT Hub (메시지 1일 보관)
  ↓
EventHub Consumer (장애 발생 시!)
  ↓
DB 저장
```

**문제:** EventHub Consumer 다운 → 데이터 손실 가능

### 해결책: 옵션 A - Dead Letter Queue (선택됨) ⭐

**간단한 구조:**
```
IoT Hub
├─ ✅ 성공 → DB 저장
└─ ❌ 실패 → Dead Letter Queue (자동 보관)
```

**장점:**
- ✅ 간단한 구현 (1시간, Portal 설정 + 코드 1개 메서드)
- ✅ 비용 거의 없음
- ✅ 프로덕션 표준
- ✅ 수동 복구 가능

**구현 예정:**
1. Azure Portal에서 IoT Hub → Message routing → Dead Letter Queue 활성화
2. EventHub Consumer에 DLQ 모니터링 메서드 추가
3. DLQ에 메시지 있으면 경고 및 재처리 옵션

**대안 (검토 및 제외):**
- 옵션 B: 다중 Consumer (구현 3-4시간, 비용 3배, 복잡도 높음)

---

## 📊 데이터 흐름 요약

### 센서 데이터 생성 ~ DB 저장 완전 흐름

```
[센서 시뮬레이터]
├─ 1초마다 모든 센서 이벤트 생성
├─ 바스켓 위치 조회 (BasketMovement)
├─ 감지 범위 내 바스켓 찾기 (0.5m 범위)
├─ detected_basket_id, signal 결정
├─ event 생성 (basket_id, signal, position_x 포함)
└─ IoT Hub로 메시지 전송

        ↓
[Azure IoT Hub]
└─ 메시지 버퍼 (1일 보관)

        ↓
[EventHub Consumer (Backend)]
├─ 메시지 수신 (거의 실시간)
├─ 최근 이벤트 메모리 캐시 (2000개 유지)
├─ 배치 버퍼에 추가
│  - 10개 모이거나
│  - 1초 경과 시
└─ _save_batch_to_db() 호출 (별도 스레드)

        ↓
[DB 저장 (PostgreSQL)]
├─ SensorEvent 객체 생성
├─ timestamp, zone_id, basket_id, sensor_id, signal, speed, position_x
├─ db.add_all(sensor_events)
├─ db.commit() ← 실제 DB 저장!
└─ 저장 완료 로그 + TEST 조회

        ↓
[Frontend API]
├─ GET /sensor-events → DB에서 조회
├─ basket_id로 필터링 가능
└─ 시각화/분석
```

---

## 🔍 데이터 검증 결과

### 현재 상태 (2026-02-02 실행 기준)
```
센서 이벤트 수신: 지속적으로 증가 중 (14,000개 이상)
DB 저장: ✅ 정상 작동
  - 로그: "✅ [시간] N개 이벤트 DB 저장 완료"
  - 주기: ~1-2초마다 배치 저장

저장 데이터:
  - timestamp: ✅ ISO 형식 (2026-02-02T...)
  - zone_id: ✅ (01-PK, 02-SO 등)
  - basket_id: ✅ (BASKET-00001, None)
  - sensor_id: ✅ (01-PK-001-S001 등)
  - signal: ✅ (true/false 동적)
  - speed: ✅ (0.0 ~ 50.0)
  - position_x: ✅ (센서 위치, 미터 단위)
```

---

## 📝 다음 단계

### 즉시 (1-2시간)
1. ✅ **완료**: sensor_data_generator.py 수정 + 배포
2. ✅ **완료**: Dockerfile 수정
3. ✅ **완료**: Docker 이미지 빌드 및 ACR 푸시
4. ⏳ **예정**: Dead Letter Queue 설정 (Portal 5분 + 코드 1시간)

### 단기 (다음 세션)
1. DLQ 모니터링 메서드 구현
2. 테스트: Consumer 강제 중지 후 DLQ 메시지 확인
3. DLQ 복구 로직 구현

### 중기 (향후)
1. 캐싱 전략 (Redis)
2. 성능 모니터링 대시보드
3. API 인증 추가

---

## 🎯 기술 결정 이유

### position_y 제거 ✅
- **이유**: 실제로 사용되지 않음, 모델 단순화 목표
- **영향**: DB 스키마 마이그레이션 불필요 (nullable 컬럼이었음)

### basket_id, position_x 추가 ✅
- **이유**: 센서 이벤트의 완전성 확보
- **설계**: 센서가 이미 알고 있는 정보, 낭비 줄임
- **효과**: DB에서 바스켓 경로 추적 가능

### Dead Letter Queue 선택 ✅
- **이유**: 단순, 비용 효율, 프로덕션 표준
- **대안**: 다중 Consumer (과도한 복잡도)
- **계획**: 필요 시 나중에 확장 가능

---

## 📌 주의사항

### 배포 시
- `deploy-to-vm.ps1` 자동 실행
- ACR 로그인 필요 (admin 자격증명 사용 중)
- 이미지 다운로드 ~ 모듈 재시작: ~30초

### DB 데이터
- sensor_events 테이블: 계속 증가 (보존 정책 필요)
- 배치 저장으로 인한 1-2초 딜레이 존재
- 감지하지 못한 바스켓은 basket_id=NULL

### 모니터링
- Backend 로그: `sudo iotedge logs logistics-backend -f`
- VM 모듈 상태: `sudo iotedge list`
- DB 행 수: PostgreSQL 직접 조회

---

**작성일**: 2026년 2월 2일
**상태**: 배포 완료, Dead Letter Queue 구현 대기
**담당자**: Development Team
