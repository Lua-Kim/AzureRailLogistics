# 시스템 보완 제안

## 📋 개요

현재 Azure IoT Edge 기반 철도 물류 시스템이 기본적으로 작동 중이지만, 
프로덕션 환경으로 나아가기 위해 필요한 개선 사항들을 정리했습니다.

---

## 🔴 높은 우선순위 (필수)

### 1. 데이터 영속성

**현재 상태**:
```
Event Hub → Backend (메모리) → 최대 2,000개 캐시
시스템 재시작 시 데이터 손실
```

**문제점**:
- 서버 재시작하면 모든 이벤트 데이터 사라짐
- 과거 데이터 조회 불가능
- 분석/모니터링 데이터 부족

**개선 방안**:
```
Event Hub → Backend → PostgreSQL (저장)
          → 메모리 캐시 (조회 성능)
```

**필요 작업**:
- 새 테이블: `sensor_events` (timestamp, basket_id, position_x, position_y 등)
- 배치 저장: 100개씩 묶어서 DB 저장
- 인덱싱: timestamp, basket_id로 빠른 조회

**예상 영향**: 저장소 필요 (월 ~100MB), 쿼리 성능 고려

---

### 2. 에러 처리 및 재시도 로직

**현재 상태**:
```python
# 실패하면 그냥 멈춤
await self.iot_client.send_message_to_output(message)
```

**문제점**:
- 네트워크 오류 시 복구 불가
- 에러 메시지가 불명확
- 모듈 충돌 시 자동 재시작 안 됨

**개선 방안**:
```
1. 재시도 로직 (exponential backoff)
   - 1초 → 2초 → 4초 → 최대 32초
   
2. 구체적 에러 로깅
   - ConnectionError, TimeoutError 구분
   - Sentry/Application Insights 연동
   
3. Circuit Breaker 패턴
   - 계속 실패하면 일시 중지
   - 주기적 재시도
```

**필요 작업**:
- decorator 작성: `@retry_with_backoff`
- 로깅 강화: 각 단계별 상세 로그
- Health check endpoint 추가

**예상 시간**: 3-4시간

---

### 3. 인증 & 보안

**현재 상태**:
```
GET /zones → 누구나 접근 가능 (공개)
```

**문제점**:
- API가 완전히 노출됨
- 악의적 요청 차단 불가
- 프로덕션 환경 부적합

**개선 방안**:

**옵션 A: JWT 토큰 (빠름)**
```python
# 로그인 → 토큰 발급 → API 호출 시 토큰 검증
POST /login → {"access_token": "..."}
GET /zones (Bearer Token 필요)
```
- 구현: 2-3시간
- 비용: 0

**옵션 B: Azure AD (엔터프라이즈)**
```python
# Azure AD에서 토큰 검증
from azure.identity import DefaultAzureCredential
```
- 구현: 4-5시간
- 비용: 무료 (Azure 구독)
- 장점: SSO 지원

**필요 작업**:
- 로그인 엔드포인트 추가
- 미들웨어에서 토큰 검증
- React에 로그인 화면 추가

---

### 4. 입력값 검증

**현재 상태**:
```python
@app.post("/simulator/reset")
async def reset():
    # 입력값 검증 없음
```

**문제점**:
- 잘못된 데이터로 API 호출 가능
- SQL Injection 위험 (일부)
- 타입 불일치 오류

**개선 방안**:
```python
from pydantic import BaseModel, Field, validator

class BasketCreateRequest(BaseModel):
    line_id: str = Field(..., min_length=1, max_length=50)
    position_x: float = Field(..., ge=0, le=10000)
    position_y: float = Field(..., ge=0, le=10000)
    
    @validator('line_id')
    def validate_line_id(cls, v):
        if not v.startswith('01-') and not v.startswith('02-'):
            raise ValueError('Invalid line_id format')
        return v
```

**필요 작업**:
- 모든 요청 모델에 검증 규칙 추가
- 응답 모델도 명시화
- API 문서에 예시 추가

**예상 시간**: 2시간

---

## 🟡 중간 우선순위 (권장)

### 5. 로깅 & 모니터링

**현재 상태**:
```python
print(f"Event received: {event}")  # 구조화되지 않음
```

**개선 방안**:

**1. 구조화된 로깅**:
```python
import logging
import json

logger = logging.getLogger(__name__)

# ❌ 현재
print("Event received")

# ✅ 개선
logger.info("event_received", extra={
    "basket_id": "basket_001",
    "line_id": "01-PK-001",
    "timestamp": datetime.utcnow().isoformat()
})
```

**2. Azure Application Insights 통합**:
```python
from opencensus.ext.azure.log_exporter import AzureLogHandler

handler = AzureLogHandler(connection_string='...')
logger.addHandler(handler)
```
- 클라우드에서 로그 수집
- 검색/분석 가능
- 경고 설정 가능

**3. 실시간 경고**:
```
에러 발생 → Application Insights → Email/SMS 알림
```

**필요 작업**:
- logging 설정 파일 작성
- Application Insights 리소스 생성
- 경고 규칙 설정

**예상 시간**: 4-5시간
**예상 비용**: 무료~$50/월

---

### 6. API 문서화

**현재 상태**:
```
FastAPI에 자동 생성 가능하지만, 미사용 중
```

**개선 방안**:
```python
# FastAPI는 기본으로 Swagger UI 제공
# http://20.196.224.42:8000/docs

@app.get("/zones", 
    summary="모든 존 정보 조회",
    description="물류센터의 모든 존(Zone) 정보를 반환합니다",
    tags=["Zones"]
)
async def get_zones():
    """
    Zone 정보 조회
    
    Returns:
        - zone_id: 존 ID
        - zone_name: 존 이름
        - lines: 해당 존의 라인 목록
    """
```

**필요 작업**:
- docstring 추가
- 응답 예시 추가
- error code 문서화

**예상 시간**: 1.5시간

---

### 7. 설정 관리

**현재 상태**:
```python
# 여러 파일에 흩어져 있음
DATABASE_URL = "postgresql://..."
IOT_HUB_CONNECTION_STRING = os.getenv("IOT_HUB_CONNECTION_STRING")
```

**개선 방안**:

**config.py 중앙화**:
```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    IOT_HUB_CONNECTION_STRING: str
    EVENTHUB_CONNECTION_STRING: str
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()

# 사용
from config import settings
database_url = settings.DATABASE_URL

# 프리셋 백업용 SQLite도 자동 생성됨
# - logistics_presets.db (로컬 백업)
# - PostgreSQL: facility_presets, preset_zones 테이블
```

**필요 작업**:
- Settings 클래스 작성
- 모든 하드코딩된 값 제거
- 환경별 설정 (.env.dev, .env.prod)

**예상 시간**: 1.5시간

---

### 8. 단위 테스트

**현재 상태**:
```
테스트 없음
```

**개선 방안**:

**pytest 기본 테스트**:
```python
# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from backend_main import app

client = TestClient(app)

def test_get_zones():
    response = client.get("/zones")
    assert response.status_code == 200
    assert "zones" in response.json()

def test_get_baskets():
    response = client.get("/baskets")
    assert response.status_code == 200
    assert "baskets" in response.json()

def test_simulator_start():
    response = client.post("/simulator/start")
    assert response.status_code == 200
    assert response.json()["status"] == "started"
```

**필요 작업**:
- pytest 설치
- 기본 엔드포인트 테스트 작성
- Mock DB 설정
- GitHub Actions에서 자동 실행

**예상 시간**: 3-4시간
**커버리지 목표**: 60% 이상

---

## 🟢 낮은 우선순위 (향후)

### 9. 캐싱 전략

**선택지**: Redis 도입
```
/zones, /baskets → Redis 캐시 (TTL 60초)
```

**효과**: API 응답 속도 10배 향상
**비용**: Redis 인스턴스 월 $20+

---

### 10. DB 성능 최적화

**필요 인덱싱**:
```sql
CREATE INDEX idx_sensor_events_timestamp ON sensor_events(timestamp DESC);
CREATE INDEX idx_sensor_events_basket_id ON sensor_events(basket_id);
CREATE INDEX idx_baskets_line_id ON baskets(line_id);
```

---

### 11. 프론트엔드 개선

**추가 기능**:
- 📊 대시보드 통계 (처리량, 평균 속도)
- 🔔 실시간 알림 (병목 지점 감지)
- 📈 시간별 그래프
- 🎯 검색/필터 기능

---

### 12. CI/CD 파이프라인

**GitHub Actions**:
```yaml
# .github/workflows/deploy.yml
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
      - run: docker build...
      - run: docker push...
```

---

### 13. 다중 IoT Edge 지원

**구조**:
```
여러 물류센터 → 각각 IoT Edge Device → 중앙 IoT Hub
```

**필요 변경**: 
- Device ID 추가 필드
- Multi-tenancy 지원

---

### 14. 프로덕션 준비

**보안**:
- SSL/TLS 인증서 (HTTPS)
- Rate Limiting
- CORS 설정

**운영**:
- 정기 백업
- 로그 아카이빙
- 재해 복구 계획

---

## 📊 우선순위 vs 난이도 매트릭스

```
난이도
  ↑
  │   [3]인증  [8]테스트  [13]다중Device
  │        
  │   [1]영속성  [14]프로덕션
  │  [2]에러처리  [7]설정
  │              [5]로깅    [9]캐싱
  │   [4]검증   [6]문서     [10]DB최적화
  └──────────────────────────────────→
     (낮음)  우선순위  (높음)
```

---

## 🚀 권장 추진 순서

### Phase 1 (즉시, 1주일)
1. **[높음-1] 데이터 영속성** → 센서 이벤트 DB 저장
2. **[높음-3] 기본 인증** → JWT 토큰

### Phase 2 (다음 2주)
3. **[높음-2] 에러 처리** → 재시도 로직
4. **[중간-5] 로깅** → Application Insights

### Phase 3 (다음 1개월)
5. **[중간-8] 단위 테스트** → 60% 커버리지
6. **[중간-7] 설정 관리** → 중앙화

### Phase 4 (향후)
- 캐싱, CI/CD, 프로덕션 준비 등

---

## 💡 즉시 시작 가능 (오늘)

**코드 없이 할 수 있는 것**:

1. **Azure Monitor 설정**
   - Portal → Application Insights 생성
   - 연결 문자열 기록

2. **NSG 보안 강화**
   - 특정 IP만 포트 8000 허용

3. **API 문서화 시작**
   - 각 엔드포인트별 목적 정리

4. **설정 파일 분석**
   - 하드코딩된 값 찾기 (`grep -r "admin123"`)

5. **테스트 케이스 설계**
   - 필수 테스트 목록 작성

---

**질문이 있으면 각 항목별로 깊이 있게 설명해드릴 수 있습니다!**

최종 업데이트: 2026년 1월 29일
