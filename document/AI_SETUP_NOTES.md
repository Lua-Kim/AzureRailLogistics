# AI 대상 문서 - AzureRailLogistics 프로젝트 설정 및 구조

---

## 1. 프로젝트 간략 소개

# AzureRailLogistics - 물류센터 실시간 시뮬레이션 및 모니터링 시스템

## 📋 프로젝트 개요

**목적**: Azure 클라우드 기반의 물류센터 바스켓 운송 시뮬레이션 및 센서 데이터 수집 시스템

**범주**
사용자 설정으로 다양한 센터 규모 설정이 가능함.
1개의 센터를 대상으로 추후 여러 센터와 본사 규모로 확대 예정

**현재 1개 센터 대상 프로젝트 구성**:
- 🎨 **Frontend**: React 기반 실시간 시각화
- 🔧 **Backend**: Python FastAPI 서버 (데이터 관리 및 API)
- 📡 **Sensor Simulator**: 물류센터 센서 데이터 생성 및 IoT Hub 전송
- ☁️ **Azure Infrastructure**: IoT Hub, EventHub, PostgreSQL

---

## 2. 개발 환경

로컬에서 개발하다가 Azure Cloud 시스템으로 마이그레이션했음. 
소스코드는 로컬과 Azure VM 2곳에 존재함.

---

## 3. 프로젝트 구조 (실시간 변경되므로 참조만 할 것)

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
│   ├── README.md               # 프로젝트 설명
│   ├── ARCHITECTURE_DESIGN_DECISIONS.md  # 아키텍처 결정사항
│   ├── AZURE_IOT_EDGE_SETUP.md # Azure 배포 가이드
│   └── ...
│
└── .env                        # 환경 변수 (git ignore)
```

---

## 4. 데이터 흐름

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

## 5. VM 리눅스 우분투 명령 안내

⚠️ **모든 Docker 관련 명령어에 sudo 필수**

```bash
# Docker Compose 실행
sudo docker-compose up -d

# 실행 중인 컨테이너 확인
sudo docker ps

# 컨테이너 로그 확인
sudo docker logs -f container_name

# 컨테이너 중지
sudo docker stop container_name

# 컨테이너 제거
sudo docker rm container_name
```

### 파일 관리 명령어

```bash
# 파일 내용 보기
cat filename

# 파일 편집 (nano)
nano filename
# 저장: Ctrl+O → Enter
# 종료: Ctrl+X

# 파일 편집 (vi/vim)
vi filename
vim filename
# 수정 모드: i
# 저장: Esc → :wq

# 파일 삭제
rm filename

# 디렉토리 삭제 (내용 포함)
rm -r directoryname

# 파일 존재 확인
ls -l filename
[ -f filename ] && echo "exists" || echo "not found"
```

---

## 6. 환경 변수 (.env)

### 주요 설정값

**PostgreSQL**
- Host: azpostgredb.postgres.database.azure.com
- User: logis_admin
- Port: 5432
- Database: postgres
- Password: !postgres16
- URL: postgresql://logis_admin:!postgres16@azpostgredb.postgres.database.azure.com:5432/postgres

**Azure VM**
- IP: 20.41.123.99
- Username: azure_admin
- Password: /!Azureadmin2026

**필수 환경변수** (소스코드 필요)
- AZ_POSTGRE_DATABASE_URL
- IOT_HUB_DEVICE_CONNECTION_STRING
- EVENTHUB_CONNECTION_STRING

---

**문서 최종 업데이트**: 2026-02-04
**대상**: AI 모델 (메모리 손실 시 이 문서 참조)
