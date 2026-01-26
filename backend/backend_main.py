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
import random
import asyncio

# sensor_simulator 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sensor_simulator'))
from basket_manager import BasketPool
from sensor_data_generator import SensorDataGenerator
from basket_movement import BasketMovement

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
print("Kafka Consumer 인스턴스 생성 완료")

# 센서 데이터 생성기 인스턴스 (새로 생성)
sensor_generator = None
sensor_generator_thread = None

# Basket Pool 인스턴스 (나중에 zones 설정으로 초기화)
basket_pool = None

# 센서 시뮬레이터 상태
simulator_running = False

# 바스켓 이동 시뮬레이터 인스턴스
movement_simulator = None

# 바스켓 풀 최대 한도 (메모리 보호용)
MAX_POOL_SIZE = 20000

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
    
    # BasketPool 초기화 (초기 배치 없이 빈 상태로 시작)
    basket_pool = BasketPool(pool_size=1000)
    print(f"Basket Pool 초기화 완료: {len(basket_pool.get_all_baskets())}개 바스켓")

async def recycle_baskets_task():
    """백그라운드 작업: 도착(arrived)한 바스켓을 주기적으로 회수하여 재사용 가능하게 만듦"""
    print("[Recycler] 바스켓 회수 시스템 가동")
    while True:
        try:
            await asyncio.sleep(5)  # 5초마다 확인
            if basket_pool:
                baskets = basket_pool.get_all_baskets()
                for b_id, basket in baskets.items():
                    if basket['status'] == 'arrived':
                        # 상태를 available로 변경하여 다시 투입 가능하도록 리셋
                        basket_pool.update_basket_status(b_id, 'available')
                        # print(f"[Recycler] {b_id} 회수 완료 (Arrived -> Available)")
        except Exception as e:
            print(f"[Recycler] 오류 발생: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 Kafka Consumer 시작"""
    global simulator_running, sensor_generator, sensor_generator_thread, movement_simulator
    
    init_data_db()  # 데이터베이스 초기화
    
    # BasketPool 초기화
    db = next(data_db())
    try:
        initialize_basket_pool(db)
        
        # BasketMovement 초기화를 위한 zones 정보 조회
        zones = logis_data_db.get_all_zones(db)
        zones_config = [
            {
                "zone_id": z.zone_id,
                "zone_name": z.name,
                "lines": z.lines,
                "length": z.length,
                "sensors": z.sensors
            }
            for z in zones
        ]
    finally:
        db.close()
    
    # 바스켓 이동 시뮬레이터 시작
    movement_simulator = BasketMovement(basket_pool, zones_config)
    movement_simulator.start()
    print("Basket Movement Simulator 시작 완료")
    
    # 센서 데이터 생성기 생성 (공유된 movement_simulator 주입)
    sensor_generator = SensorDataGenerator(basket_pool=basket_pool, basket_movement=movement_simulator)
    
    # Kafka Consumer 시작
    consumer.start()
    print("Kafka Consumer 시작 완료")
    
    # 센서 시뮬레이션 자동 시작 (별도 스레드)
    sensor_generator.start()
    simulator_running = True
    print("Backend 서버 시작 완료, 센서 시뮬레이션 실행 중")
    
    # 바스켓 회수 백그라운드 태스크 시작
    asyncio.create_task(recycle_baskets_task())

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 Kafka Consumer와 센서 시뮬레이터 중지"""
    try:
        sensor_generator.stop()  # 센서 생성기 중지
    except Exception as e:
        print(f"센서 생성기 중지 오류: {e}")
    
    try:
        if movement_simulator:
            movement_simulator.stop()
    except Exception as e:
        print(f"Movement Simulator 중지 오류: {e}")
    
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
async def get_latest_events(count: int = 10, only_active: bool = False):
    """최근 센서 이벤트 조회"""
    # consumer.latest_events 리스트를 직접 사용하여 안전하게 조회
    if hasattr(consumer, 'latest_events') and consumer.latest_events:
        if only_active:
            # active인 것만 필터링하여 뒤에서부터 count개 가져오기
            active_events = [e for e in consumer.latest_events if e.get("signal") == True]
            events = active_events[-count:]
        else:
            events = consumer.latest_events[-count:]
    else:
        events = []
        
    print(f"[API] /events/latest 반환: {len(events)}개 이벤트 (프론트엔드 요청)")
    if events:
        print(f"  모든 이벤트 정보:")
        for idx, event in enumerate(events):
            print(f"    [{idx+1}] {event}")
    else:
        print("  반환할 이벤트 없음")
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
    zones = logis_data_db.get_all_zones(db)
    print(f"[API] /zones 반환: {len(zones)}개 존")
    if zones:
        print(f"  첫번째 존: {zones[0]}")
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
    print(f"\n[API] /zones/config/batch 요청 수신 (프리셋 저장)")
    print(f"  - 수신된 존 개수: {len(zones_list)}")
    for i, zone in enumerate(zones_list):
        print(f"    [{i+1}] {zone.zone_id} ({zone.name}): Lines={zone.lines}, Sensors={zone.sensors}")
        
    try:
        # 1. 기존 존 ID 목록 조회
        existing_zones = db.query(LogisticsZone).all()
        existing_ids = {z.zone_id for z in existing_zones}
        new_ids = {z.zone_id for z in zones_list}
        
        # 2. 삭제 대상 (기존에는 있지만 새 요청에는 없는 존)
        to_delete = existing_ids - new_ids
        if to_delete:
            # 연관된 라인 먼저 삭제 후 존 삭제
            db.query(LogisticsLine).filter(LogisticsLine.zone_id.in_(to_delete)).delete(synchronize_session=False)
            db.query(LogisticsZone).filter(LogisticsZone.zone_id.in_(to_delete)).delete(synchronize_session=False)

        # 3. 생성 및 업데이트
        for zone_data in zones_list:
            # 존 조회
            zone = db.query(LogisticsZone).filter(LogisticsZone.zone_id == zone_data.zone_id).first()
            
            if zone:
                # 업데이트
                zone.name = zone_data.name
                zone.lines = zone_data.lines
                zone.length = zone_data.length
                zone.sensors = zone_data.sensors
                # 기존 라인 삭제 (라인 설정이 바뀌었을 수 있으므로 재생성)
                deleted_count = db.query(LogisticsLine).filter(LogisticsLine.zone_id == zone_data.zone_id).delete(synchronize_session=False)
                print(f"    - Zone {zone_data.zone_id}: 기존 라인 {deleted_count}개 삭제됨")
            else:
                # 생성
                zone = LogisticsZone(
                    zone_id=zone_data.zone_id,
                    name=zone_data.name,
                    lines=zone_data.lines,
                    length=zone_data.length,
                    sensors=zone_data.sensors
                )
                db.add(zone)
            
            # 라인 생성 (001, 002... 형식)
            sensors_per_line = zone_data.sensors // zone_data.lines if zone_data.lines > 0 else 0
            new_lines = []
            for i in range(zone_data.lines):
                line_id = f"{zone_data.zone_id}-{i+1:03d}"
                new_lines.append(LogisticsLine(
                    zone_id=zone_data.zone_id,
                    line_id=line_id,
                    length=zone_data.length,
                    sensors=sensors_per_line
                ))
            db.add_all(new_lines)
            print(f"    - Zone {zone_data.zone_id}: 새 라인 {len(new_lines)}개 생성됨")
            
        db.commit()
        print("  - 배치 저장 완료 (DB Commit)")
        return db.query(LogisticsZone).all()
        
    except Exception as e:
        db.rollback()
        print(f"  - 배치 저장 실패: {e}")
        raise e

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
    
    # 라인 결정 로직: line_id가 있으면 검증, 없으면 해당 존의 라인 중 랜덤 선택 (로드 밸런싱)
    target_lines = []
    if request_data.line_id:
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
        target_lines = [request_data.line_id]
    else:
        # 라인 미지정 시 해당 존의 모든 라인 조회
        lines = db.query(LogisticsLine).filter(
            LogisticsLine.zone_id == request_data.zone_id
        ).all()
        if not lines:
            return {
                "success": False,
                "created_count": 0,
                "baskets": [],
                "message": f"No lines found in zone '{request_data.zone_id}'"
            }
        target_lines = [l.line_id for l in lines]
    
    # 사용 가능한 바스켓 조회
    available_baskets = basket_pool.get_available_baskets()
    
    # [동적 확장] 요청 수량이 가용 수량보다 많으면 풀 확장
    if len(available_baskets) < request_data.count:
        current_total = len(basket_pool.get_all_baskets())
        needed = request_data.count - len(available_baskets)
        
        # 최대 한도 체크
        if current_total >= MAX_POOL_SIZE:
            print(f"[System] 풀 확장 불가: 최대 한도({MAX_POOL_SIZE}) 도달")
        else:
            expand_amount = needed + 50  # 여유분
            # 한도 초과 방지
            if current_total + expand_amount > MAX_POOL_SIZE:
                expand_amount = MAX_POOL_SIZE - current_total
            
            print(f"[System] 바스켓 부족. {expand_amount}개 추가 생성 (Auto Expansion)")
            if hasattr(basket_pool, 'expand_pool') and expand_amount > 0:
                basket_pool.expand_pool(expand_amount)
                available_baskets = basket_pool.get_available_baskets()
    
    # 바스켓 할당
    created_baskets = []
    for i in range(request_data.count):
        basket = available_baskets[i]
        basket_id = basket["basket_id"]
        
        # 라인 선택 (지정된 경우 하나만, 아니면 랜덤 로드 밸런싱)
        selected_line_id = random.choice(target_lines)
        
        # assign_basket 호출: zone_id, line_id, destination 설정
        destination = request_data.destination or request_data.zone_id
        assigned_basket = basket_pool.assign_basket(
            basket_id,
            request_data.zone_id,
            selected_line_id,
            destination
        )
        
        if assigned_basket:
            created_baskets.append(assigned_basket)
            print(f"[바스켓 생성] {basket_id} assigned to {request_data.zone_id}-{selected_line_id} → {destination}")
    
    return {
        "success": True,
        "created_count": len(created_baskets),
        "baskets": created_baskets,
        "message": f"Successfully created {len(created_baskets)} baskets"
    }

@app.get("/baskets")
async def get_all_baskets(db: Session = Depends(data_db)):
    if basket_pool is None:
        print("[API] /baskets: Basket pool not initialized")
        return {
            "error": "Basket pool not initialized",
            "baskets": [],
            "statistics": {}
        }
    baskets = basket_pool.get_all_baskets()
    enriched_baskets = []
    for basket in baskets.values():
        basket_copy = basket.copy()
        if basket_copy["zone_id"]:
            zone = db.query(LogisticsZone).filter(LogisticsZone.zone_id == basket_copy["zone_id"]).first()
            if zone:
                basket_copy["line_length"] = zone.length
        
        # 실시간 위치 정보 병합 (Movement Simulator가 실행 중일 때)
        if movement_simulator:
            pos_info = movement_simulator.get_basket_position(basket_copy["basket_id"])
            if pos_info:
                basket_copy["position_meters"] = pos_info.get("position_meters", 0)
                basket_copy["progress_percent"] = pos_info.get("progress_percent", 0)
                
        enriched_baskets.append(basket_copy)
    stats = basket_pool.get_statistics()
    print(f"[API] /baskets 반환: {len(enriched_baskets)}개 바스켓, 통계: {stats} (프론트엔드 요청)")
    # if enriched_baskets:
    #     print(f"  모든 바스켓 정보:")
    #     for idx, basket in enumerate(enriched_baskets):
    #         print(f"    [{idx+1}] {basket}")
    # else:
    #     print("  반환할 바스켓 없음")
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

@app.get("/baskets/movements")
async def get_basket_movements():
    """현재 이동 중인 바스켓들의 실시간 위치 정보"""
    if movement_simulator:
        return movement_simulator.get_all_positions()
    return []

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
        if movement_simulator:
            movement_simulator.start()
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
        if movement_simulator:
            movement_simulator.stop()
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
    latest_time = None
    if hasattr(consumer, 'latest_events') and consumer.latest_events:
        latest_time = consumer.latest_events[-1].get("timestamp")

    return {
        "running": simulator_running,
        "events_received": consumer.get_event_count(),
        "latest_event_time": latest_time
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
