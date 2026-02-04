# Architecture Design Decisions & Future Considerations

## 1. 바스켓 투입/제거 시스템

### 현재 구현
- **입구**: 라인 시작점(0m)에서만 투입
- **출구**: 라인 끝점에서만 제거
- **이동**: 순차적으로 다음 구역으로 이동

### 미래 요구사항: 중간 투입/제거

사용자 요구사항:
```
- 라인 중간(예: 50m 지점)에서도 바스켓 투입 가능
- 라인 중간(예: 30m 지점)에서 빠져나가기
- 다른 구역의 라인으로 직접 이동
```

#### 복잡도 분석

| 항목 | 영향 | 난이도 |
|------|------|--------|
| **경로 추적** | 각 바스켓이 "라인의 어느 위치"인지 관리 필요 | 높음 |
| **센서 동기화** | 센서는 전체 길이(0~50m)에 분산 → 중간 투입/제거 시 센서와의 관계 복잡화 | 높음 |
| **동적 라우팅** | 현재 "Zone 순서대로 자동 이동" 방식과 충돌 | 높음 |
| **코드 복잡도** | 투입/이동/제거 로직 전반 재설계 필요 | 매우 높음 |

#### 권장사항

**현재**: 기본 기능(입구-출구) 유지
- MVP 관점: 센서 데이터 수집과 병목 감지가 주목적
- 충분성: 입구→출구 흐름으로도 물류 시뮬레이션 충분
- 실익: 개발 시간 대비 낮음

**향후 개선 옵션**:
1. **Option A**: 라인 중간의 특정 센서 위치에서만 제거 허용 (부분 구현)
2. **Option B**: "자동화 운송 라인" vs "택배 분류" 같이 시나리오별 모드 분리
3. **Option C**: 비즈니스 요구사항 명확화 후 선별 구현

---


## 2. 멀티센터 시스템 아키텍처

### 현재 상태 - 싱글센터
```
VM (20.196.224.42)
├── Backend (port 8000)
├── Sensor Simulator (port 5001)
├── Frontend (React dev, port 3000)
└── Azure PostgreSQL (공유)
```
Backend (서버)                Frontend (클라이언트)
───────────────────────────────────────────────
VM:8000 (1개)    ←────────    브라우저 A
                 ←────────    브라우저 B  
                 ←────────    브라우저 C
                 ←────────    모바일 앱
                 
                 (다대일 구조: N:1)

### 멀티센터 확장 옵션

#### Option 1: 센터별 독립 VM (추천 - 운영 안정성)

```
센터 A (VM 1)              센터 B (VM 2)
├── Backend:8000          ├── Backend:8000
├── Sensor Sim:5001       ├── Sensor Sim:5001
└── Frontend:3000         └── Frontend:3000
        ↓                        ↓
   ┌───────────────────────────────┐
   │  Azure PostgreSQL             │
   │  (공유 DB - 센터별 분리)       │
   └───────────────────────────────┘
```

**장점:**
- ✅ 각 센터 독립적 운영 (한 센터 장애 → 다른 센터 영향 없음)
- ✅ 네트워크 지연 최소화 (로컬 백엔드 호출)
- ✅ 확장 용이
- ✅ 각 센터의 특화된 설정 가능

**단점:**
- ❌ VM 비용 증가
- ❌ 관리 포인트 증가

---

#### Option 2: 중앙화 백엔드 (비용 효율)

```
VM (1개)
├── Backend (port 8000, Multi-Tenant)
│   ├── /api/center-A/...
│   ├── /api/center-B/...
│   └── /api/center-C/...
├── Sensor Sim A (port 5001)
├── Sensor Sim B (port 5002)
└── Sensor Sim C (port 5003)
        ↓
   Azure PostgreSQL
   (센터별 schema 분리)
```

**장점:**
- ✅ VM 1개로 여러 센터 운영
- ✅ 비용 효율적
- ✅ 중앙에서 통합 모니터링 가능

**단점:**
- ❌ 한 센터 장애 → 전체 영향 가능
- ❌ 코드 복잡도 증가 (Multi-Tenant 로직)
- ❌ 백엔드 코드 리팩토링 필요

---

#### Option 3: 하이브리드 (권장 - 장기)

```
Frontend (중앙 1개)
    ↓
API Gateway / Load Balancer
    ↓
Backend 1     Backend 2     Backend 3
(센터 A)      (센터 B)      (센터 C)
    ↓           ↓            ↓
Sensor A     Sensor B      Sensor C
    ↓───────────┴────────────↓
      Azure PostgreSQL
      (각 센터 DB 독립)
```

**장점:**
- ✅ 중앙 대시보드에서 전체 모니터링
- ✅ 각 센터는 독립적 운영
- ✅ 가장 실무적이고 확장성 우수

**단점:**
- ❌ 초기 구축 복잡도 높음
- ❌ API Gateway 별도 구성 필요

---

### 권장 이행 로드맵

**단기 (현재 ~ 3개월)**: Option 1
- 현재 코드를 각 센터마다 배포
- 복잡도 최소화
- 빠른 검증

**중기 (3~6개월)**: Option 3로 마이그레이션
- 중앙 대시보드 구축
- API Gateway 추가
- 통합 모니터링

**장기 (6개월 이상)**: Option 2로 최적화
- 비용 절감 필요시
- 통합 관리 자동화

---

## 3. Backend-Frontend 관계

### 아키텍처 모델: 일대다 (1:N)

```
Backend (서버)                Frontend (클라이언트)
─────────────────────────────────────────────
VM:8000 (1개)    ←─────    브라우저 A
                 ←─────    브라우저 B  
                 ←─────    브라우저 C
                 ←─────    모바일 앱
```

**핵심:**
- Backend = 서버 (1개만 띄우면 됨)
- Frontend = 클라이언트 (여러 개 동시 접속 가능)
- 다대일 구조 (N:1)

### 현재 배포

```
VM (20.196.224.42:8000) = 백엔드 서버
  ↑
  ├─ 로컬 React dev (http://localhost:3000) 
  │  └─ REACT_APP_API_URL=http://20.196.224.42:8000
  └─ 다른 IP의 브라우저도 접속 가능
```

### 멀티센터 배포 (권장)

```
중앙 Frontend                여러 Backend
(1개 React)          ─────────┬─────────
"센터 선택" 기능             ├─ 센터 A:8000
  ↓                          ├─ 센터 B:8000
  센터 A 선택               └─ 센터 C:8000
  └─> Backend A와 통신
```

**구현 예시:**
```javascript
// Frontend에서
const [selectedCenter, setSelectedCenter] = useState('A');

const API_BASE = selectedCenter === 'A' 
  ? 'http://센터A-IP:8000'
  : 'http://센터B-IP:8000';

// 모든 API 호출은 동적으로 API_BASE 사용
const response = await fetch(`${API_BASE}/api/...`);
```

---

## 4. 데이터베이스 설계 (멀티센터 대비)

### 현재
```sql
CREATE TABLE logistics_zones (
  zone_id VARCHAR PRIMARY KEY,
  name VARCHAR,
  ...
);
```

### 멀티센터 개선안
```sql
CREATE TABLE logistics_zones (
  center_id VARCHAR NOT NULL,  -- "CENTER-A", "CENTER-B"
  zone_id VARCHAR NOT NULL,
  name VARCHAR,
  ...
  PRIMARY KEY (center_id, zone_id),
  INDEX idx_center_zone (center_id, zone_id)
);
```

### API 경로 설계

**멀티센터 지원 API:**
```
GET    /centers/{center_id}/zones
POST   /centers/{center_id}/baskets/create
GET    /centers/{center_id}/bottlenecks
POST   /centers/{center_id}/simulator/start
```

---

## 5. 의사결정 체크리스트

멀티센터 시스템 도입 전 결정 사항:

- [ ] **센터 개수**: 현재? 예정?
- [ ] **통합 대시보드 필요**: Yes/No
- [ ] **센터별 독립성**: 중요도?
- [ ] **비용 vs 복잡도**: 우선순위?
- [ ] **일정**: 언제까지 구축?

---

## 6. 다음 단계

1. **즉시 (현재)**: 기본 기능 검증
   - 1개 센터에서 시스템 안정화
   - 센서-바스켓 동기화 검증

2. **단기 (1개월)**: 멀티센터 준비
   - 코드에 center_id 필드 추가
   - API 경로에 센터 ID 포함 리팩토링

3. **중기 (3개월)**: 멀티센터 배포
   - Option 1 또는 3 선택 후 구현
   - 각 센터별 설정 문서화

---

**작성일**: 2026-02-02  
**관련 시스템**: Azure Rail Logistics  
**상태**: 설계 검토 단계
