from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from kafka_consumer import SensorEventConsumer
from database import init_data_db, data_db, logis_data_db
from models import LogisticsZone, LogisticsLine
from schemas import (
    LogisticsZoneCreate, 
    LogisticsZone as LogisticsZoneSchema,
    BasketCreateRequest,
    BasketCreateResponse
)
from typing import List
import sys
import os
import threading

# sensor_simulator 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sensor_simulator'))
from basket_manager import BasketPool
from simple_sensor_generator import SimpleSensorDataGenerator

app = FastAPI(title="Azure Rail Logistics Backend")

# 모든 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """모든 HTTP 요청 로깅"""
    print(f"\n>>> 요청: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"<<< 응답: {response.status_code}")
    return response

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kafka Consumer 인스턴스
consumer = SensorEventConsumer()

# 센서 데이터 생성기 인스턴스 (새로 생성)
sensor_generator = None
sensor_generator_thread = None

# Basket Pool 인스턴스 (나중에 zones 설정으로 초기화)
basket_pool = None

# 센서 시뮬레이터 상태
simulator_running = False

def initialize_basket_pool(db: Session):
    """zones 설정을 기반으로 바스켓 풀 초기화"""
    global basket_pool
    
    zones = logis_data_db.get_all_zones(db)
    
    # zones-lines 설정 구성 (라인 길이 정보 포함)
    zones_lines_config = []
    for zone in zones:
        zone_config = {
            'zone_id': zone.zone_id,
            'lines': [
                {
                    'line_id': line.line_id,
                    'length': line.length if hasattr(line, 'length') else 0
                }
                for line in (zone.zone_lines if zone.zone_lines else [])
            ]
        }
        zones_lines_config.append(zone_config)
    
    # BasketPool 초기화 (라인별로 랜덤 개수 배분, 라인 길이 제약 준수)
    basket_pool = BasketPool(pool_size=200, zones_lines_config=zones_lines_config)
    print(f"Basket Pool 초기화 완료: {len(basket_pool.get_all_baskets())}개 바스켓")

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 Kafka Consumer 시작"""
    global simulator_running, sensor_generator, sensor_generator_thread
    
    init_data_db()  # 데이터베이스 초기화
    
    # BasketPool 초기화
    db = next(data_db())
    try:
        initialize_basket_pool(db)
    finally:
        db.close()
    
    # 센서 데이터 생성기 새로 생성 (간단한 버전)
    sensor_generator = SimpleSensorDataGenerator()
    
    # Kafka Consumer 시작
    consumer.start()
    
    # 센서 시뮬레이션 자동 시작 (별도 스레드)
    sensor_generator.start()
    simulator_running = True
    print("Backend 서버 시작 완료, 센서 시뮬레이션 실행 중")

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 Kafka Consumer와 센서 시뮬레이터 중지"""
    try:
        sensor_generator.stop()  # 센서 생성기 중지
    except Exception as e:
        print(f"센서 생성기 중지 오류: {e}")
    
    try:
        consumer.stop()
    except Exception as e:
        print(f"컨슈머 중지 오류: {e}")
    
    print("Backend 서버 종료")

@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "status": "ok",
        "message": "Azure Rail Logistics Backend",
        "events_received": consumer.get_event_count()
    }

@app.get("/events/latest")
async def get_latest_events(count: int = 10):
    """최근 센서 이벤트 조회"""
    events = consumer.get_latest_events(count)
    return {
        "count": len(events),
        "events": events
    }

@app.get("/events/stats")
async def get_event_stats():
    """이벤트 통계"""
    events = consumer.latest_events
    
    if not events:
        return {"message": "No events received yet"}
    
    # 간단한 통계
    signal_true_count = sum(1 for e in events if e.get("signal") == True)
    signal_false_count = sum(1 for e in events if e.get("signal") == False)
    
    zones = {}
    for event in events:
        zone_id = event.get("zone_id")
        if zone_id:
            zones[zone_id] = zones.get(zone_id, 0) + 1
    
    return {
        "total_events": len(events),
        "signal_true": signal_true_count,
        "signal_false": signal_false_count,
        "zones": zones
    }

@app.get("/zones/summary")
async def get_zones_summary():
    """존별 요약 정보"""
    events = consumer.latest_events
    
    if not events:
        return []
    
    # 존별로 데이터 집계
    zone_data = {}
    for event in events:
        zone_id = event.get("zone_id")
        if not zone_id:
            continue
            
        if zone_id not in zone_data:
            zone_data[zone_id] = {
                "zone_id": zone_id,
                "data_points": 0,
                "total_throughput": 0,
                "total_speed": 0,
                "speed_count": 0,
                "bottleneck_count": 0
            }
        
        zone_data[zone_id]["data_points"] += 1
        
        if event.get("signal"):
            zone_data[zone_id]["total_throughput"] += 1
            speed = event.get("speed", 0)
            if speed > 0:
                zone_data[zone_id]["total_speed"] += speed
                zone_data[zone_id]["speed_count"] += 1
            
            # 속도가 낮으면 병목으로 간주
            if speed < 30:
                zone_data[zone_id]["bottleneck_count"] += 1
    
    # 평균 계산 및 결과 생성
    result = []
    for zone_id, data in zone_data.items():
        avg_speed = data["total_speed"] / data["speed_count"] if data["speed_count"] > 0 else 0
        result.append({
            "zone_id": zone_id,
            "total_throughput": data["total_throughput"],
            "avg_speed": round(avg_speed, 2),
            "data_points": data["data_points"],
            "bottleneck_count": data["bottleneck_count"]
        })
    
    return result

@app.get("/bottlenecks")
async def get_bottlenecks():
    """병목 현상 감지 - signal이 true이면서 속도가 30% 이하인 이벤트 반환"""
    events = consumer.latest_events
    
    if not events:
        return []
    
    # signal이 true이면서 속도가 30% 이하인 이벤트를 병목으로 간주
    bottleneck_events = [e for e in events if e.get("signal") == True and e.get("speed", 100) < 30]
    
    # zone_id별로 병목 점수 계산
    bottleneck_zones = {}
    for event in bottleneck_events:
        zone_id = event.get("zone_id")
        if zone_id:
            if zone_id not in bottleneck_zones:
                bottleneck_zones[zone_id] = {
                    "zone_id": zone_id,
                    "aggregated_id": f"BOTTLENECK-{zone_id}",
                    "bottleneck_score": 0.0,
                    "count": 0
                }
            bottleneck_zones[zone_id]["count"] += 1
            bottleneck_zones[zone_id]["bottleneck_score"] = min(1.0, bottleneck_zones[zone_id]["count"] / 10)
    
    # 점수 내림차순 정렬
    result = sorted(bottleneck_zones.values(), key=lambda x: x["bottleneck_score"], reverse=True)
    return result

@app.get("/sensors/history")
async def get_sensor_history(zone_id: str = None, count: int = 100):
    """센서 히스토리 조회 - 원본 센서 데이터 반환 (집계 X)"""
    events = consumer.latest_events
    
    # zone_id로 필터링
    if zone_id:
        filtered_events = [e for e in events if e.get("zone_id") == zone_id]
    else:
        filtered_events = events
    
    # 최근 count개만 반환
    return filtered_events[-count:]

# ============ ZONES 설정 API ============

@app.get("/zones")
async def get_zones(db: Session = Depends(data_db)):
    """모든 존 조회"""
    zones = logis_data_db.get_all_zones(db)
    return zones

@app.post("/zones")
async def create_zone(zone: LogisticsZoneCreate, db: Session = Depends(data_db)):
    """새 존 생성 (존 정보만, 라인은 별도로)"""
    return logis_data_db.save_zone(db, zone)

@app.post("/lines")
async def create_lines(lines: List[dict], db: Session = Depends(data_db)):
    """라인 저장 (배치)"""
    return logis_data_db.save_lines(db, lines)

@app.get("/zones/config", response_model=List[LogisticsZoneSchema])
async def get_zones_config(db: Session = Depends(data_db)):
    """현재 zones 설정 조회"""
    zones = logis_data_db.get_all_zones(db)
    return zones

@app.post("/zones/config", response_model=LogisticsZoneSchema)
async def create_zone_with_lines(zone: LogisticsZoneCreate, db: Session = Depends(data_db)):
    """새 zone 추가 (라인도 자동 생성)"""
    return logis_data_db.save_zone_with_lines(db, zone)

@app.put("/zones/config/{zone_id}", response_model=LogisticsZoneSchema)
async def update_zone(zone_id: str, zone: LogisticsZoneCreate, db: Session = Depends(data_db)):
    """zone 업데이트"""
    db_zone = logis_data_db.update_zone_data(db, zone_id, zone)
    if not db_zone:
        return {"error": "Zone not found"}
    return db_zone

@app.delete("/zones/config/{zone_id}")
async def delete_zone(zone_id: str, db: Session = Depends(data_db)):
    """zone 삭제"""
    result = logis_data_db.delete_zone_data(db, zone_id)
    if not result:
        return {"error": "Zone not found"}
    return {"deleted": result}

@app.post("/zones/config/batch")
async def set_zones_batch(zones_list: List[LogisticsZoneCreate], db: Session = Depends(data_db)):
    """zones 전체 설정 (기존 데이터 전부 교체)"""
    result = logis_data_db.save_batch_zones(db, zones_list)
    return result

@app.post("/api/baskets/create")
async def create_baskets(
    request_data: "BasketCreateRequest",
    db: Session = Depends(data_db)
):
    """
    바스켓 생성 및 라인에 할당
    
    Args:
        zone_id: 구역 ID (예: IB-01)
        line_id: 라인 ID (예: IB-01-001)
        count: 생성할 바스켓 수
        destination: 목적지 (선택)
    
    Returns:
        생성된 바스켓 목록
    """
    if basket_pool is None:
        return {
            "success": False,
            "created_count": 0,
            "baskets": [],
            "message": "Basket pool not initialized"
        }
    
    # zone_id와 line_id 검증
    zone = db.query(LogisticsZone).filter(LogisticsZone.zone_id == request_data.zone_id).first()
    if not zone:
        return {
            "success": False,
            "created_count": 0,
            "baskets": [],
            "message": f"Zone '{request_data.zone_id}' not found"
        }
    
    line = db.query(LogisticsLine).filter(
        LogisticsLine.zone_id == request_data.zone_id,
        LogisticsLine.line_id == request_data.line_id
    ).first()
    if not line:
        return {
            "success": False,
            "created_count": 0,
            "baskets": [],
            "message": f"Line '{request_data.line_id}' in zone '{request_data.zone_id}' not found"
        }
    
    # 사용 가능한 바스켓 조회
    available_baskets = basket_pool.get_available_baskets()
    
    if len(available_baskets) < request_data.count:
        return {
            "success": False,
            "created_count": 0,
            "baskets": [],
            "message": f"Not enough available baskets. Available: {len(available_baskets)}, Requested: {request_data.count}"
        }
    
    # 바스켓 할당
    created_baskets = []
    for i in range(request_data.count):
        basket = available_baskets[i]
        basket_id = basket["basket_id"]
        
        # assign_basket 호출: zone_id, line_id, destination 설정
        destination = request_data.destination or request_data.zone_id
        assigned_basket = basket_pool.assign_basket(
            basket_id,
            request_data.zone_id,
            request_data.line_id,
            destination
        )
        
        if assigned_basket:
            created_baskets.append(assigned_basket)
            print(f"[바스켓 생성] {basket_id} assigned to {request_data.zone_id}-{request_data.line_id} → {destination}")
    
    return {
        "success": True,
        "created_count": len(created_baskets),
        "baskets": created_baskets,
        "message": f"Successfully created {len(created_baskets)} baskets"
    }

@app.get("/baskets")
async def get_all_baskets(db: Session = Depends(data_db)):
    """전체 바스켓 조회 (라인 길이 정보 포함)"""
    if basket_pool is None:
        return {
            "error": "Basket pool not initialized",
            "baskets": [],
            "statistics": {}
        }
    
    baskets = basket_pool.get_all_baskets()
    
    # 각 바스켓에 라인 길이 정보 추가
    enriched_baskets = []
    for basket in baskets.values():
        basket_copy = basket.copy()
        
        # 존이 할당된 경우 DB에서 라인 길이 조회
        if basket_copy["zone_id"]:
            zone = db.query(LogisticsZone).filter(LogisticsZone.zone_id == basket_copy["zone_id"]).first()
            if zone:
                basket_copy["line_length"] = zone.length
        
        enriched_baskets.append(basket_copy)
    
    # 통계 정보 계산
    stats = basket_pool.get_statistics()
    
    return {
        "count": len(enriched_baskets),
        "baskets": enriched_baskets,
        "statistics": stats
    }

@app.get("/baskets/{basket_id}")
async def get_basket(basket_id: str):
    """특정 바스켓 조회"""
    basket = basket_pool.get_basket(basket_id)
    if basket:
        return basket
    return {"error": "Basket not found"}

# ============ 센서 시뮬레이터 제어 API ============

@app.post("/simulator/start")
async def start_simulator():
    """센서 시뮬레이션 시작 (Kafka로 센서 데이터 전송)"""
    global simulator_running
    
    if simulator_running:
        return {
            "status": "already_running",
            "message": "센서 시뮬레이션이 이미 실행 중입니다.",
            "running": True
        }
    
    try:
        sensor_generator.start()
        simulator_running = True
        return {
            "status": "started",
            "message": "센서 시뮬레이션이 시작되었습니다.",
            "running": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"시뮬레이션 시작 실패: {str(e)}",
            "running": False
        }

@app.post("/simulator/stop")
async def stop_simulator(request: Request):
    """센서 시뮬레이션 중지 (Kafka로의 센서 데이터 전송 중지)"""
    global simulator_running
    
    print(f"\n=== /simulator/stop API 호출 ===")
    print(f"Method: {request.method}")
    print(f"URL: {request.url}")
    print(f"Client: {request.client}")
    print(f"Headers: {dict(request.headers)}")
    print(f"현재 simulator_running: {simulator_running}")
    
    if not simulator_running:
        result = {
            "status": "already_stopped",
            "message": "센서 시뮬레이션이 이미 중지 상태입니다.",
            "running": False
        }
        print(f"Result: {result}")
        return result
    
    try:
        sensor_generator.stop()
        simulator_running = False
        result = {
            "status": "stopped",
            "message": "센서 시뮬레이션이 중지되었습니다.",
            "running": False
        }
        print(f"Result: {result}")
        return result
    except Exception as e:
        result = {
            "status": "error",
            "message": f"시뮬레이션 중지 실패: {str(e)}",
            "running": True
        }
        print(f"Result: {result}")
        return result

@app.get("/simulator/status")
async def get_simulator_status():
    """센서 시뮬레이션 상태 조회"""
    return {
        "running": simulator_running,
        "events_received": consumer.get_event_count(),
        "latest_event_time": consumer.get_latest_event_time() if consumer.latest_events else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

