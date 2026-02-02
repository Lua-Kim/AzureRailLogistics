# Azure Rail Logistics - VM 빠른 배포 스크립트
# 수정된 코드를 Docker 이미지로 빌드하고 VM에 배포

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Azure Rail Logistics - VM 배포 시작" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
$ACR_NAME = "containerogis.azurecr.io"
$VM_IP = "20.196.224.42"
$SSH_KEY = "C:\Users\EL0100\Downloads\edge-runtime-vm_key.pem"

# 1. Docker 이미지 빌드
Write-Host "`n[1/5] Docker 이미지 빌드 중..." -ForegroundColor Yellow

Write-Host "  - Backend 빌드..." -ForegroundColor Gray
docker build -t ${ACR_NAME}/logistics-backend:latest ./backend
if ($LASTEXITCODE -ne 0) { throw "Backend 빌드 실패" }

Write-Host "  - Sensor Simulator 빌드..." -ForegroundColor Gray
docker build -t ${ACR_NAME}/logistics-sensor-simulator:latest ./sensor_simulator
if ($LASTEXITCODE -ne 0) { throw "Sensor Simulator 빌드 실패" }

Write-Host "  ✅ 빌드 완료" -ForegroundColor Green

# 2. ACR에 푸시
Write-Host "`n[2/5] ACR에 이미지 푸시 중..." -ForegroundColor Yellow

Write-Host "  - Backend 푸시..." -ForegroundColor Gray
docker push ${ACR_NAME}/logistics-backend:latest
if ($LASTEXITCODE -ne 0) { throw "Backend 푸시 실패" }

Write-Host "  - Sensor Simulator 푸시..." -ForegroundColor Gray
docker push ${ACR_NAME}/logistics-sensor-simulator:latest
if ($LASTEXITCODE -ne 0) { throw "Sensor Simulator 푸시 실패" }

Write-Host "  ✅ 푸시 완료" -ForegroundColor Green

# 3. VM에서 이전 컨테이너 중지
Write-Host "`n[3/5] VM 모듈 중지 중..." -ForegroundColor Yellow
ssh -i $SSH_KEY azureuser@${VM_IP} "sudo iotedge stop logistics-backend; sudo iotedge stop logistics-sensor-simulator"
Start-Sleep -Seconds 3
Write-Host "  ✅ 모듈 중지 완료" -ForegroundColor Green

# 4. 새 이미지 pull
Write-Host "`n[4/5] 새 이미지 다운로드 중..." -ForegroundColor Yellow
ssh -i $SSH_KEY azureuser@${VM_IP} "sudo docker pull ${ACR_NAME}/logistics-backend:latest; sudo docker pull ${ACR_NAME}/logistics-sensor-simulator:latest"
Write-Host "  ✅ 이미지 다운로드 완료" -ForegroundColor Green

# 5. 모듈 재시작
Write-Host "`n[5/5] VM 모듈 재시작 중..." -ForegroundColor Yellow
ssh -i $SSH_KEY azureuser@${VM_IP} "sudo iotedge restart logistics-backend; sudo iotedge restart logistics-sensor-simulator"
Start-Sleep -Seconds 5
Write-Host "  ✅ 모듈 재시작 완료" -ForegroundColor Green

# 6. deployment.json 생성 (환경 변수 치환)
Write-Host "`n[6/6] Deployment 설정 생성 중..." -ForegroundColor Yellow
python convert_deployment.py
if ($LASTEXITCODE -ne 0) { throw "Deployment.json 생성 실패" }
Write-Host "  ✅ Deployment.json 생성 완료" -ForegroundColor Green

# 7. VM에 deployment.json 복사 및 적용
Write-Host "`n[7/7] VM에 설정 적용 중..." -ForegroundColor Yellow
scp -i $SSH_KEY deployment.json azureuser@${VM_IP}:/tmp/deployment.json
ssh -i $SSH_KEY azureuser@${VM_IP} "sudo cp /tmp/deployment.json /etc/iotedge/config/deployment.json && sudo systemctl restart iotedge"
Start-Sleep -Seconds 10
Write-Host "  ✅ 설정 적용 완료" -ForegroundColor Green

# 8. 상태 확인
Write-Host "로그 확인: ssh -i '$SSH_KEY' azureuser@${VM_IP} 'sudo iotedge logs logistics-backend -f'" -ForegroundColor Gray
