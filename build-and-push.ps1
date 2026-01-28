# Azure Container Registry 빌드 및 푸시 스크립트

param(
    [Parameter(Mandatory=$true)]
    [string]$AcrName,
    
    [Parameter(Mandatory=$false)]
    [string]$Tag = "latest"
)

$ACR_LOGIN_SERVER = "$AcrName.azurecr.io"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Azure IoT Edge 이미지 빌드 시작" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "ACR: $ACR_LOGIN_SERVER"
Write-Host "Tag: $Tag"
Write-Host ""

# ACR 로그인
Write-Host "ACR에 로그인 중..." -ForegroundColor Yellow
az acr login --name $AcrName
if ($LASTEXITCODE -ne 0) {
    Write-Host "ACR 로그인 실패!" -ForegroundColor Red
    exit 1
}

# 백엔드 이미지 빌드
Write-Host ""
Write-Host "백엔드 이미지 빌드 중..." -ForegroundColor Yellow
docker build -t ${ACR_LOGIN_SERVER}/logistics-backend:${Tag} -f backend/Dockerfile backend/
if ($LASTEXITCODE -ne 0) {
    Write-Host "백엔드 이미지 빌드 실패!" -ForegroundColor Red
    exit 1
}

Write-Host "백엔드 이미지 푸시 중..." -ForegroundColor Yellow
docker push ${ACR_LOGIN_SERVER}/logistics-backend:${Tag}
if ($LASTEXITCODE -ne 0) {
    Write-Host "백엔드 이미지 푸시 실패!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 백엔드 이미지 완료" -ForegroundColor Green

# 센서 시뮬레이터 이미지 빌드
Write-Host ""
Write-Host "센서 시뮬레이터 이미지 빌드 중..." -ForegroundColor Yellow
docker build -t ${ACR_LOGIN_SERVER}/logistics-sensor-simulator:${Tag} -f sensor_simulator/Dockerfile sensor_simulator/
if ($LASTEXITCODE -ne 0) {
    Write-Host "센서 시뮬레이터 이미지 빌드 실패!" -ForegroundColor Red
    exit 1
}

Write-Host "센서 시뮬레이터 이미지 푸시 중..." -ForegroundColor Yellow
docker push ${ACR_LOGIN_SERVER}/logistics-sensor-simulator:${Tag}
if ($LASTEXITCODE -ne 0) {
    Write-Host "센서 시뮬레이터 이미지 푸시 실패!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 센서 시뮬레이터 이미지 완료" -ForegroundColor Green

# 완료
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "모든 이미지가 성공적으로 푸시되었습니다!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "푸시된 이미지:"
Write-Host "  - ${ACR_LOGIN_SERVER}/logistics-backend:${Tag}"
Write-Host "  - ${ACR_LOGIN_SERVER}/logistics-sensor-simulator:${Tag}"
Write-Host ""
Write-Host "다음 단계:"
Write-Host "  1. deployment.template.json 파일의 이미지 경로 업데이트"
Write-Host "  2. IoT Edge 디바이스에 배포: az iot edge set-modules ..."
