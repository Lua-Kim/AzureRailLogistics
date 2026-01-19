@echo off
REM 센서-백엔드-프론트엔드 통합 테스트 스크립트

echo.
echo ========================================
echo 센서-백엔드-프론트엔드 통합 연동 테스트
echo ========================================
echo.

REM 프로젝트 루트 경로
set PROJECT_ROOT=c:\Users\EL0100\Desktop\AzureRailLogistics

REM 1. Docker 서비스 확인 및 시작
echo [Step 1] Docker 서비스 확인 중...
docker ps -a | findstr postgres > nul
if errorlevel 1 (
    echo Docker 서비스를 시작합니다...
    cd %PROJECT_ROOT%
    docker-compose up -d
    timeout /t 10
) else (
    echo Docker 서비스가 이미 실행 중입니다.
)

REM 2. 백엔드 환경 확인
echo.
echo [Step 2] 백엔드 환경 확인 중...
cd %PROJECT_ROOT%\backend
python -m pip install -r requirements.txt > nul 2>&1

REM 3. 백엔드 서버 시작 (별도 터미널)
echo.
echo [Step 3] 백엔드 서버 시작 중 (포트 8000)...
start "Backend" cmd /k "cd %PROJECT_ROOT%\backend && python backend_main.py"
timeout /t 5

REM 4. 프론트엔드 환경 확인
echo.
echo [Step 4] 프론트엔드 환경 확인 중...
cd %PROJECT_ROOT%\frontend
call npm install > nul 2>&1

REM 5. 프론트엔드 개발 서버 시작 (별도 터미널)
echo.
echo [Step 5] 프론트엔드 개발 서버 시작 중 (포트 3000)...
start "Frontend" cmd /k "cd %PROJECT_ROOT%\frontend && npm start"
timeout /t 5

REM 6. 통합 테스트 실행
echo.
echo [Step 6] 통합 테스트 실행 중...
cd %PROJECT_ROOT%
python integration_test.py

echo.
echo ========================================
echo 테스트 완료
echo ========================================
echo.
echo [주소]
echo - 백엔드: http://localhost:8000
echo - 프론트엔드: http://localhost:3000
echo - API 문서: http://localhost:8000/docs
echo.
pause
