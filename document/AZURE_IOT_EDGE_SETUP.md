# Azure IoT Edge 설정 가이드 (GUI 기반)

## 1단계: Azure Portal에서 리소스 그룹 생성

1. **Azure Portal 접속** (https://portal.azure.com)
2. **홈 화면**에서 `리소스 그룹` 검색
3. **'+ 만들기'** 버튼 클릭
   - **구독**: 사용 중인 구독 선택
   - **리소스 그룹 이름**: `2dt-final-team5`
   - **지역**: `한국 중부 (Korea Central)`
4. **검토 + 만들기** → **만들기** 클릭

## 2단계: Container Registry 생성

1. **Azure Portal**에서 `Container Registry` 검색
2. **'+ 만들기'** 버튼 클릭
3. **기본 정보 입력**
   - **리소스 그룹**: `2dt-final-team5` 선택
   - **레지스트리 이름**: `containerogis`
   - **지역**: `한국 중부`
   - **SKU**: `기본`
4. **검토 + 만들기** → **만들기**
5. 배포 완료 후, **리소스로 이동** 클릭
6. **설정 > 액세스 키** 탭에서
   - **관리 사용자 활성화** 토글 ON
   - 로그인 서버, 사용자 이름, 암호 복사 후 저장

## 3단계: IoT Hub 생성

1. **Azure Portal**에서 `IoT Hub` 검색
2. **'+ 만들기'** 버튼 클릭
3. **기본 정보 입력**
   - **리소스 그룹**: `2dt-final-team5` 선택
   - **IoT 허브 이름**: `LogisticsIoTHub`
   - **지역**: `한국 중부`
   - **가격 및 규모 계층**: `S1`
4. **검토 + 만들기** → **만들기**
5. 배포 완료 후 **리소스로 이동** 클릭

## 4단계: IoT Edge 디바이스 등록

1. **IoT Hub 리소스** 열기
2. **관리 > 디바이스** 탭 선택
3. **'+ 디바이스 추가'** 버튼 클릭
4. **디바이스 정보 입력**
   - **디바이스 ID**: `logistics-edge-01`
   - **인증 유형**: `대칭 키`
   - **IoT Edge 런타임**: **활성화** 토글 ON
5. **저장** 클릭
6. 생성된 디바이스 클릭 후
   - **연결 문자열 (기본 키)** 복사 후 저장

## 5단계: Docker 이미지 빌드 및 푸시

### 로컬 컴퓨터에서:

1. **PowerShell 또는 터미널** 열기
2. **프로젝트 디렉토리**로 이동: `cd C:\Users\EL0100\Desktop\AzureRailLogistics`
3. **다음 명령 실행**:
```powershell
# ACR 로그인 (패스워드는 Azure Portal > Container Registry > 액세스 키에서 확인)
echo "YOUR_PASSWORD" | docker login containerogis.azurecr.io -u containerogis --password-stdin

# 백엔드 이미지 빌드 및 푸시
docker build -t containerogis.azurecr.io/logistics-backend:latest -f backend/Dockerfile backend/
docker push containerogis.azurecr.io/logistics-backend:latest

# 센서 시뮬레이터 이미지 빌드 및 푸시
docker build -t containerogis.azurecr.io/logistics-sensor-simulator:latest -f sensor_simulator/Dockerfile .
docker push containerogis.azurecr.io/logistics-sensor-simulator:latest
```

> **팁**: `build-and-push.ps1` 스크립트가 있으면 `./build-and-push.ps1`로 한 번에 실행 가능

## 6단계: IoT Edge 런타임 설치 (Edge 디바이스에서)

### Windows Edge Device:

1. **PowerShell (관리자 권한)** 열기
2. **다음 명령 실행**:
```powershell
# IoT Edge 설치 스크립트 실행
. {Invoke-WebRequest -useb https://aka.ms/iotedge-win} | Invoke-Expression; `
Deploy-IoTEdge -ContainerOs Windows
```
3. **설치 완료** 후 시스템 재시작
4. **PowerShell (관리자 권한)** 다시 열기
5. **IoT Edge 구성**:
```powershell
Initialize-IoTEdge -ManualConnectionString -ConnectionString "YOUR_CONNECTION_STRING"
```
(5단계에서 복사한 연결 문자열 붙여넣기)

### Linux Edge Device:

1. **터미널** 열기
2. **다음 명령 실행**:
```bash
# Microsoft 패키지 저장소 추가
curl https://packages.microsoft.com/config/ubuntu/20.04/multiarch/prod.list > ./microsoft-prod.list
sudo cp ./microsoft-prod.list /etc/apt/sources.list.d/
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo cp ./microsoft.gpg /etc/apt/trusted.gpg.d/

# 설치
sudo apt-get update
sudo apt-get install aziot-edge

# 구성
sudo iotedge config mp --connection-string "YOUR_CONNECTION_STRING"
sudo iotedge config apply
```

## 7단계: 배포 매니페스트 설정

1. **Azure Portal**에서 **IoT Hub** 열기
2. **관리 > 디바이스** 탭 선택
3. **logistics-edge-01** 클릭
4. **모듈 설정** 탭 선택
5. **'+ 모듈 추가'** → **Azure Container Registry 모듈** 선택
6. **모듈 정보 입력**:
   - **IoT Edge 모듈 이름**: `logistics-backend`
   - **이미지 URI**: `containerogis.azurecr.io/logistics-backend:latest`
   - **컨테이너 생성 옵션**: 필요한 포트, 환경 변수 설정
7. 동일한 방식으로 `logistics-sensor-simulator` 모듈 추가
8. **검토 + 만들기** → **만들기** 클릭

## 8단계: 배포 상태 모니터링

### Azure Portal에서 확인:

1. **IoT Hub** 열기
2. **관리 > 디바이스** 탭 선택
3. **logistics-edge-01** 클릭
4. **모듈** 탭에서 각 모듈의 상태 확인
   - ✅ **실행 중**: 모듈이 정상 작동
   - ⚠️ **다른 상태**: 상태 상세 보기 클릭하여 오류 확인

### Edge Device에서 직접 확인:

**Windows PowerShell (관리자 권한)**:
```powershell
# 실행 중인 모듈 목록 확인
iotedge list

# 특정 모듈 로그 확인
iotedge logs logistics-backend
iotedge logs logistics-sensor-simulator
```

**Linux 터미널**:
```bash
# 실행 중인 모듈 목록 확인
sudo iotedge system status

# 특정 모듈 로그 확인
sudo iotedge logs logistics-backend
```

## 9단계: IoT Hub 메시지 모니터링

1. **Azure Portal**에서 **IoT Hub** 열기
2. **모니터링 > 메시지** 또는 **디바이스 > 모듈** 탭에서
   - 실시간 메시지 흐름 확인
   - 모듈 간 통신 상태 확인

또는 **PowerShell**에서:
```powershell
# IoT Hub 메시지 모니터링
az iot hub monitor-events --hub-name LogisticsIoTHub --device-id logistics-edge-01
```

## 트러블슈팅 가이드

### 문제 1: 이미지 Pull 실패

**증상**: 모듈이 "ImagePullBackoff" 상태

**해결 방법**:
1. **Azure Portal > Container Registry > 저장소** 확인
   - 이미지가 실제로 업로드되었는지 확인
2. **Azure Portal > IoT Hub > 디바이스 > 모듈** 확인
   - ACR 자격증명이 올바르게 입력되었는지 확인
   - 이미지 URI 스펠링 확인
3. **Edge Device에서**:
```powershell
# ACR 재로그인
az acr login --name containerogis
```

### 문제 2: 모듈이 시작되지 않음

**증상**: 모듈이 "종료됨" 또는 "실패" 상태

**해결 방법**:
1. **Azure Portal > IoT Hub > 디바이스 > 모듈** 클릭
   - 상태 상세 보기에서 오류 메시지 확인
2. **Edge Device에서 로그 확인**:
```powershell
# 모듈 로그 확인
iotedge logs logistics-backend

# 더 자세한 로그 확인
iotedge logs logistics-backend --tail 100
```
3. **deployment.json 재검토**
   - 환경 변수 설정 확인
   - 포트 바인딩 확인
   - 볼륨 마운트 경로 확인

### 문제 3: 모듈 간 통신 불가

**증상**: 모듈이 실행되지만 메시지가 전달되지 않음

**해결 방법**:
1. **호스트명 사용**: `localhost` 대신 **컨테이너 이름** 사용
   - 예: `kafka`, `postgres` 등 Docker 컨테이너 이름으로 통신
2. **네트워크 정책 확인**:
   - deployment.json의 `HostConfig.PortBindings` 확인
   - 필요한 포트가 모두 설정되었는지 확인


## 빠른 참조 - 자동화 스크립트

프로젝트에 포함된 **build-and-push.ps1** 스크립트를 사용하면 모든 이미지를 자동으로 빌드하고 푸시할 수 있습니다:

```powershell
# PowerShell에서 실행
./build-and-push.ps1
```

## 문제 4: 포트 바인딩 충돌

**증상**: 컨테이너가 시작되지 않고 포트 오류 메시지 발생

**해결 방법**:
1. **현재 사용 중인 포트 확인**:
```powershell
# Windows
netstat -ano | findstr :5000

# Linux
netstat -tuln | grep 5000
```
2. **deployment.json에서 포트 변경**
3. IoT Hub에서 모듈 설정 업데이트

## 성공 확인 체크리스트

- [x] Azure Portal에서 리소스 그룹(2dt-final-team5) 생성 완료
- [x] Container Registry(containerogis) 생성 및 접근 키 확보
- [x] IoT Hub(LogisticsIoTHub) 생성 완료
- [x] IoT Edge Device(logistics-edge-01) 등록 및 연결 문자열 확보
- [x] 로컬에서 Docker 이미지 빌드 및 ACR 업로드 완료
- [x] Azure Portal에서 IoT Edge 모듈 배포 완료
- [ ] 모듈 상태 "실행 중" 확인 (약 5-10분 소요)
- [ ] IoT Hub에서 메시지 수신 확인

## 추가 리소스

| 항목 | 링크 |
|------|------|
| Azure IoT Edge 문서 | https://docs.microsoft.com/azure/iot-edge/ |
| Azure Container Registry 문서 | https://docs.microsoft.com/azure/container-registry/ |
| IoT Edge 모듈 개발 | https://docs.microsoft.com/azure/iot-edge/module-development |
| Azure IoT Hub 모니터링 | https://docs.microsoft.com/azure/iot-hub/iot-hub-operations-monitoring |
| PowerShell IoT 명령어 | https://learn.microsoft.com/en-us/powershell/module/az.iothub/ |
