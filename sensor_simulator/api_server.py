"""
센서 시뮬레이터 제어 API 서버
백엔드에서 시뮬레이터를 start/stop/reset할 수 있도록 제공
"""
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from sensor_data_generator import SensorDataGenerator
from basket_manager import BasketPool

app = FastAPI(title="Sensor Simulator Control API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 시뮬레이터 인스턴스
generator = None
basket_pool = None

def initialize_simulator():
    """시뮬레이터 초기화"""
    global generator, basket_pool
    
    if generator is None:
        print("[API Server] 시뮬레이터 초기화 중...")
        basket_pool = BasketPool(pool_size=100)
        generator = SensorDataGenerator(basket_pool=basket_pool)
        print("[API Server] 시뮬레이터 준비 완료")

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 시뮬레이터 초기화 (자동 시작 없음)"""
    initialize_simulator()
    # 자동 시작 제거 - 사용자가 프론트엔드에서 수동으로 시작해야 함
    print("[API Server] 시뮬레이터 초기화 완료 (자동 시작 안함)")

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 시뮬레이터 중지"""
    if generator and generator.is_running:
        generator.stop()
        print("[API Server] 시뮬레이터 중지 완료")

@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "status": "ok",
        "service": "Sensor Simulator Control API"
    }

@app.get("/simulator/status")
async def get_status():
    """시뮬레이터 상태 조회"""
    if generator is None:
        return {
            "running": False,
            "message": "시뮬레이터가 초기화되지 않았습니다"
        }
    
    return {
        "running": generator.is_running,
        "zones": len(generator.zones),
        "basket_pool_size": len(basket_pool.get_all_baskets()) if basket_pool else 0,
        "message": "시뮬레이터 정상 동작 중" if generator.is_running else "시뮬레이터 정지됨"
    }

@app.post("/simulator/start")
async def start_simulator():
    """시뮬레이터 시작"""
    if generator is None:
        initialize_simulator()
    
    if generator.is_running:
        return {
            "status": "already_running",
            "message": "시뮬레이터가 이미 실행 중입니다"
        }
    
    try:
        generator.start()
        return {
            "status": "success",
            "message": "시뮬레이터 시작 완료",
            "running": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"시뮬레이터 시작 실패: {str(e)}",
            "running": False
        }

@app.post("/simulator/stop")
async def stop_simulator():
    """시뮬레이터 정지"""
    if generator is None:
        return {
            "status": "not_initialized",
            "message": "시뮬레이터가 초기화되지 않았습니다"
        }
    
    if not generator.is_running:
        return {
            "status": "already_stopped",
            "message": "시뮬레이터가 이미 정지되어 있습니다"
        }
    
    try:
        generator.stop()
        return {
            "status": "success",
            "message": "시뮬레이터 정지 완료",
            "running": False
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"시뮬레이터 정지 실패: {str(e)}",
            "running": generator.is_running
        }

@app.post("/simulator/reset")
async def reset_simulator():
    """시뮬레이터 초기화 (재시작)"""
    global generator, basket_pool
    
    try:
        # 기존 시뮬레이터 정지
        if generator and generator.is_running:
            generator.stop()
        
        # 새로 초기화
        basket_pool = BasketPool(pool_size=100)
        generator = SensorDataGenerator(basket_pool=basket_pool)
        
        # 자동 시작
        generator.start()
        
        return {
            "status": "success",
            "message": "시뮬레이터 초기화 및 재시작 완료",
            "running": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"시뮬레이터 초기화 실패: {str(e)}",
            "running": False
        }

def run_api_server():
    """API 서버 실행 (별도 스레드에서)"""
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")

if __name__ == "__main__":
    print("[API Server] 센서 시뮬레이터 제어 API 서버 시작...")
    run_api_server()
