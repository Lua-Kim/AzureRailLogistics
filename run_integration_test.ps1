# 센서-백엔드-프론트엔드 통합 테스트 스크립트

$PROJECT_ROOT = "c:\Users\EL0100\Desktop\AzureRailLogistics"
$BACKEND_PORT = 8000
$FRONTEND_PORT = 3000

Write-Host "`n========================================" -ForegroundColor Blue
Write-Host " 센서-백엔드-프론트엔드 통합 연동 테스트" -ForegroundColor Blue
Write-Host "========================================`n" -ForegroundColor Blue

# Step 1: Docker 서비스 확인
Write-Host "[Step 1] Docker 서비스 확인 중..." -ForegroundColor Green

$postgresRunning = docker ps | Select-String "postgres" | Measure-Object | Select-Object -ExpandProperty Count
$kafkaRunning = docker ps | Select-String "kafka" | Measure-Object | Select-Object -ExpandProperty Count

if ($postgresRunning -eq 0 -or $kafkaRunning -eq 0) {
    Write-Host "Docker 서비스를 시작합니다..." -ForegroundColor Yellow
    Set-Location $PROJECT_ROOT
    docker-compose up -d
    Write-Host "Docker 서비스 시작 중... (15초 대기)" -ForegroundColor Yellow
    Start-Sleep -Seconds 15
} else {
    Write-Host "Docker 서비스가 이미 실행 중입니다." -ForegroundColor Green
}

# Step 2: PostgreSQL 연결 확인
Write-Host "`n[Step 2] PostgreSQL 연결 확인 중..." -ForegroundColor Green
$pgVersion = psql -h localhost -U admin -d logistics -c "SELECT version();" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "PostgreSQL 연결 실패. 재시도 중..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# Step 3: 백엔드 환경 설정
Write-Host "`n[Step 3] 백엔드 환경 설정 중..." -ForegroundColor Green
Set-Location "$PROJECT_ROOT\backend"
python -m pip install -r requirements.txt -q

# Step 4: 백엔드 서버 시작
Write-Host "`n[Step 4] 백엔드 서버 시작 중 (포트 $BACKEND_PORT)..." -ForegroundColor Green
$backendProcess = Start-Process python -ArgumentList "backend_main.py" -WindowStyle Hidden -PassThru -WorkingDirectory "$PROJECT_ROOT\backend"
Write-Host "Backend PID: $($backendProcess.Id)" -ForegroundColor Gray
Start-Sleep -Seconds 5

# Step 5: 백엔드 헬스 체크
Write-Host "`n[Step 5] 백엔드 헬스 체크 중..." -ForegroundColor Green
$retries = 5
$backendReady = $false
for ($i = 0; $i -lt $retries; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$BACKEND_PORT/" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ 백엔드 서버 준비 완료" -ForegroundColor Green
            $backendReady = $true
            break
        }
    } catch {
        Write-Host "재시도 $($i+1)/$retries..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

if (-not $backendReady) {
    Write-Host "✗ 백엔드 서버 연결 실패" -ForegroundColor Red
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# Step 6: 프론트엔드 환경 설정
Write-Host "`n[Step 6] 프론트엔드 환경 설정 중..." -ForegroundColor Green
Set-Location "$PROJECT_ROOT\frontend"
npm install -q 2>&1

# Step 7: 통합 테스트 실행
Write-Host "`n[Step 7] 통합 테스트 실행 중..." -ForegroundColor Green
Set-Location $PROJECT_ROOT
python integration_test.py

# Step 8: 결과 출력
Write-Host "`n========================================" -ForegroundColor Blue
Write-Host " 테스트 완료" -ForegroundColor Blue
Write-Host "========================================`n" -ForegroundColor Blue

Write-Host "[주소]" -ForegroundColor Cyan
Write-Host "  - 백엔드:      http://localhost:$BACKEND_PORT" -ForegroundColor Cyan
Write-Host "  - 프론트엔드:  http://localhost:$FRONTEND_PORT" -ForegroundColor Cyan
Write-Host "  - API 문서:   http://localhost:$BACKEND_PORT/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "[다음 단계]" -ForegroundColor Cyan
Write-Host "  1. 프론트엔드 개발 서버 시작 (별도 터미널):" -ForegroundColor Cyan
Write-Host "     cd $PROJECT_ROOT\frontend && npm start" -ForegroundColor Gray
Write-Host "  2. 브라우저에서 접속: http://localhost:$FRONTEND_PORT" -ForegroundColor Cyan
Write-Host ""

# 백엔드 유지
Write-Host "[백엔드 서버는 실행 중입니다. 종료하려면 Ctrl+C를 누르세요.]" -ForegroundColor Yellow
Wait-Process -Id $backendProcess.Id
