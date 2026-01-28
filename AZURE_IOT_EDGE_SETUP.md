# Azure IoT Edge 설정 가이드

## 1. Azure Container Registry 생성

```powershell
# Azure CLI 로그인
az login

# 리소스 그룹 생성
az group create --name LogisticsRG --location koreacentral

# Container Registry 생성
az acr create --resource-group LogisticsRG --name logisticsacr --sku Basic

# Admin 계정 활성화
az acr update -n logisticsacr --admin-enabled true

# 로그인 자격증명 확인
az acr credential show --name logisticsacr
```

## 2. 도커 이미지 빌드 및 푸시

### 백엔드 이미지
```powershell
# ACR에 로그인
az acr login --name logisticsacr

# 백엔드 이미지 빌드
docker build -t logisticsacr.azurecr.io/logistics-backend:latest ./backend

# 이미지 푸시
docker push logisticsacr.azurecr.io/logistics-backend:latest
```

### 센서 시뮬레이터 이미지
```powershell
# 센서 시뮬레이터 이미지 빌드
docker build -t logisticsacr.azurecr.io/logistics-sensor-simulator:latest ./sensor_simulator

# 이미지 푸시
docker push logisticsacr.azurecr.io/logistics-sensor-simulator:latest
```

## 3. Azure IoT Hub 생성

```powershell
# IoT Hub 생성
az iot hub create --resource-group LogisticsRG --name LogisticsIoTHub --sku S1

# IoT Edge 디바이스 등록
az iot hub device-identity create --hub-name LogisticsIoTHub --device-id edge-device-01 --edge-enabled
```

## 4. IoT Edge 런타임 설치 (Edge 디바이스에서)

### Windows
```powershell
# IoT Edge 다운로드 및 설치
. {Invoke-WebRequest -useb https://aka.ms/iotedge-win} | Invoke-Expression; `
Deploy-IoTEdge

# 연결 문자열 가져오기
az iot hub device-identity connection-string show --device-id edge-device-01 --hub-name LogisticsIoTHub

# IoT Edge 구성
Initialize-IoTEdge -ManualConnectionString -ConnectionString "YOUR_CONNECTION_STRING"
```

### Linux
```bash
# Microsoft 패키지 저장소 추가
curl https://packages.microsoft.com/config/ubuntu/20.04/multiarch/prod.list > ./microsoft-prod.list
sudo cp ./microsoft-prod.list /etc/apt/sources.list.d/
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo cp ./microsoft.gpg /etc/apt/trusted.gpg.d/

# IoT Edge 설치
sudo apt-get update
sudo apt-get install aziot-edge

# 연결 문자열로 구성
sudo iotedge config mp --connection-string "YOUR_CONNECTION_STRING"
sudo iotedge config apply
```

## 5. 배포 매니페스트 적용

```powershell
# .env 파일 생성 (템플릿 복사)
Copy-Item .env.template .env

# .env 파일 수정 (ACR 정보 입력)
# CONTAINER_REGISTRY_ADDRESS=logisticsacr.azurecr.io
# CONTAINER_REGISTRY_USERNAME=<username>
# CONTAINER_REGISTRY_PASSWORD=<password>

# 배포
az iot edge set-modules --device-id edge-device-01 --hub-name LogisticsIoTHub --content deployment.template.json
```

## 6. 배포 상태 확인

```powershell
# 모듈 상태 확인
az iot hub module-identity list --device-id edge-device-01 --hub-name LogisticsIoTHub

# Edge 디바이스에서 직접 확인
iotedge list
iotedge logs backend
iotedge logs sensorSimulator
```

## 7. 빠른 빌드 스크립트

### build-and-push.ps1
```powershell
# 변수 설정
$ACR_NAME = "logisticsacr"
$ACR_LOGIN_SERVER = "$ACR_NAME.azurecr.io"

# ACR 로그인
az acr login --name $ACR_NAME

# 백엔드 빌드 및 푸시
Write-Host "Building backend image..."
docker build -t ${ACR_LOGIN_SERVER}/logistics-backend:latest ./backend
docker push ${ACR_LOGIN_SERVER}/logistics-backend:latest

# 센서 시뮬레이터 빌드 및 푸시
Write-Host "Building sensor simulator image..."
docker build -t ${ACR_LOGIN_SERVER}/logistics-sensor-simulator:latest ./sensor_simulator
docker push ${ACR_LOGIN_SERVER}/logistics-sensor-simulator:latest

Write-Host "All images pushed successfully!"
```

## 8. 모니터링

```powershell
# IoT Hub 메시지 모니터링
az iot hub monitor-events --hub-name LogisticsIoTHub --device-id edge-device-01

# 특정 모듈 로그 실시간 확인
iotedge logs backend -f
```

## 트러블슈팅

### 이미지 Pull 실패
- ACR 자격증명이 올바른지 확인
- ACR에 이미지가 업로드되었는지 확인: `az acr repository list --name logisticsacr`

### 모듈이 시작되지 않음
- 로그 확인: `iotedge logs <module-name>`
- 환경 변수 확인: deployment.template.json의 Env 설정 검토

### 네트워크 연결 문제
- 모듈 간 통신은 컨테이너 이름으로 진행 (kafka, postgres 등)
- 포트 바인딩 충돌 확인

## 추가 리소스

- [Azure IoT Edge 문서](https://docs.microsoft.com/azure/iot-edge/)
- [Azure Container Registry 문서](https://docs.microsoft.com/azure/container-registry/)
- [IoT Edge 모듈 개발](https://docs.microsoft.com/azure/iot-edge/module-development)
