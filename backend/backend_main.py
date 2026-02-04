from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Integer
from typing import Optional, List
from database import init_data_db, data_db, logis_data_db
from models import LogisticsZone, LogisticsLine, SensorEvent, Preset, PresetZone
from schemas import (
    LogisticsZoneCreate, 
    LogisticsZone as LogisticsZoneSchema,
    BasketCreateRequest,
    BasketCreateResponse
)
import sys
import os
import threading
import random
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# .env 파일 로드 (Docker에서는 파일이 없을 수 있으므로 무시)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print(f"⚠️ .env 파일을 찾을 수 없습니다: {env_path}")
    print("   Docker 환경변수 또는 시스템 환경변수를 사용합니다.")

# 백엔드 폴더에 있는 basket_manager 임포트
from basket_manager import BasketPool

# ====== 다중 DB 저장용 설정 ======
# 로컬 SQLite (프론트엔드용)
LOCAL_SQLITE_URL = "sqlite:///logistics_presets.db"
local_sqlite_engine = create_engine(LOCAL_SQLITE_URL, echo=False)
LocalSQLiteSession = sessionmaker(bind=local_sqlite_engine)

# Azure PostgreSQL
AZURE_DATABASE_URL = os.getenv("AZ_POSTGRE_DATABASE_URL")
if AZURE_DATABASE_URL:
    azure_engine = create_engine(AZURE_DATABASE_URL, echo=False, pool_size=5, max_overflow=10)
    AzureSession = sessionmaker(bind=azure_engine)
else:
    AzureSession = None
    print("⚠️ AZ_POSTGRE_DATABASE_URL 없음 - Azure 동기화 비활성화")

# Sensor simulator control API base URL
SIMULATOR_API_BASE = os.getenv("SIMULATOR_API_BASE", "http://localhost:5001")
# Sensor simulator API timeout (seconds)
SIMULATOR_API_TIMEOUT = float(os.getenv("SIMULATOR_API_TIMEOUT", "30"))

app = FastAPI(title="Azure Rail Logistics Backend")

# 요청 로깅 미들웨어 (최소화: 에러만 로깅)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """최소한의 HTTP 요청 로깅"""
    response = await call_next(request)
    # 에러 응답만 로깅
    if response.status_code >= 400:
        print(f"[API] ❌ {request.method} {request.url.path}: {response.status_code}")
    return response

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# EventHub Consumer (환경변수 있을 때만 활성화)
consumer = None
if os.getenv("EVENTHUB_CONNECTION_STRING"):
    try:
        from eventhub_consumer import SensorEventConsumer
        # consumer는 나중에 basket_pool 초기화 후 생성
        print("EventHub Consumer 모듈 로드 완료 (basket_pool 초기화 후 인스턴스 생성 예정)")
    except Exception as e:
        print(f"⚠️ EventHub Consumer 모듈 로드 실패: {e}")
else:
    print("⚠️ EVENTHUB_CONNECTION_STRING 없음 - EventHub Consumer 비활성화")

# ============ 전역 변수 ============
# Basket Pool 인스턴스 (zones 설정으로 초기화)
basket_pool = None

# 바스켓 풀 최대 한도 (메모리 보호용)
MAX_POOL_SIZE = 20000

# 라인 최대 수용량 경고 임계값 (%)
MAX_LINE_CAPACITY_PERCENT = 80

# 같은 라인에서 바스켓 간 최소 간격 (초)
MIN_BASKET_INTERVAL = 3.0

# 바스켓 간 최소 거리 (미터) - 라인별 용량 계산 기준
BASKET_SPACING_M = 5.0

# 라인별 용량 정보 (초기화 시 계산, 매번 재계산 방지)
# 구조: {line_id: {"max": int, "length": float}}
line_capacity_info = {}

# 바스켓 투입 대기 큐
deployment_queue = []

# 라인별 마지막 투입 시간 (초)
line_last_deployment = {}

def initialize_basket_pool(db: Session):
    """
    zones 설정을 기반으로 바스켓 풀 초기화
    - BasketPool 인스턴스 생성
    - 라인별 속도 구간 초기화 (센서 개수 기준)
    - 라인별 최대 수용량 계산 및 저장
    """
    global basket_pool, line_capacity_info
    
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
    
    # BasketPool 초기화 (zones_lines_config 전달) - 풀 크기 축소 (필요시 확장)
    basket_pool = BasketPool(pool_size=20, zones_lines_config=zones_lines_config)
    
    # ============ 라인별 최대 수용량 계산 (초기화 시 1회만) ============
    # BASKET_SPACING_M 간격 기준으로 각 라인이 수용할 수 있는 최대 바스켓 수 계산
    line_capacity_info = {}
    for zone in zones:
        zone_lines = zone.zone_lines if zone.zone_lines else []
        for line in zone_lines:
            line_id = line.line_id
            line_length = line.length if hasattr(line, 'length') else 100
            max_capacity = int(line_length / BASKET_SPACING_M)  # BASKET_SPACING_M 간격 기준
            line_capacity_info[line_id] = {
                "max": max_capacity,
                "length": line_length
            }
    
    # ============ 구간별 속도 설정 초기화 (센서 기준 구간 분할) ============
    basket_pool.line_speed_zones = {}
    basket_pool.base_speed_mps = 1.0  # 기본 속도 1m/s
    for zone in zones:
        zone_lines = zone.zone_lines if zone.zone_lines else []
        for line in zone_lines:
            line_id = line.line_id
            line_length = line.length if hasattr(line, 'length') else 100
            
            # 센서 개수 계산 (라인의 센서 수)
            if hasattr(line, 'sensors') and line.sensors:
                # sensors가 리스트면 len(), 정수면 그대로 사용
                if isinstance(line.sensors, (list, tuple)):
                    num_segments = len(line.sensors)
                else:
                    num_segments = int(line.sensors) if line.sensors > 0 else 5
            else:
                num_segments = 5  # 센서가 없으면 기본 5개 구간
            
            # 센서 개수만큼 구간 분할
            if num_segments > 0:
                segment_length = line_length / num_segments
            else:
                segment_length = line_length
                num_segments = 1
            
            segments = []
            for i in range(num_segments):
                segments.append({
                    "start": i * segment_length,
                    "end": (i + 1) * segment_length,
                    "multiplier": random.choice([0.5, 0.8, 1.0, 1.2, 1.5])  # 속도 계수
                })
            basket_pool.line_speed_zones[line_id] = segments
    
    print(f"Basket Pool 초기화 완료: {len(basket_pool.get_all_baskets())}개 바스켓, {len(basket_pool.line_speed_zones)}개 라인 속도 구간 설정")

def get_speed_at_position(line_id: str, position_m: float) -> float:
    """
    바스켓의 현재 위치에 해당하는 구간의 속도 계수 반환
    
    Args:
        line_id: 라인 ID
        position_m: 바스켓의 현재 위치 (미터)
    
    Returns:
        속도 계수 (0.5 ~ 1.5, 기본값 1.0)
    """
    if not basket_pool or not hasattr(basket_pool, 'line_speed_zones'):
        return 1.0
    
    if line_id not in basket_pool.line_speed_zones:
        return 1.0
    
    segments = basket_pool.line_speed_zones[line_id]
    for seg in segments:
        if seg["start"] <= position_m < seg["end"]:
            return seg["multiplier"]
    
    # 마지막 구간
    if segments:
        return segments[-1]["multiplier"]
    return 1.0

async def update_basket_positions_task():
    """
    백그라운드 작업: 구간별 속도를 적용하여 바스켓 위치를 주기적으로 업데이트
    
    동작 원리:
    1. 주기적으로 moving/in_transit 상태의 모든 바스켓 확인
    2. 각 바스켓의 현재 위치에 해당하는 구간의 속도 계수 조회
    3. 실제 속도 = 기본 속도(1m/s) × 속도 계수 × 경과시간(dt)
    4. 새 위치 계산 후 라인 끝 도달 시 'arrived' 상태로 전환
    5. 앞 바스켓 때문에 이동이 멈춘 경우 병목 플래그 설정
    """
    last_time = time.time()
    
    while True:
        try:
            await asyncio.sleep(0.1)  # 100ms마다 업데이트
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # 디버깅 등으로 인해 멈췄다가 실행될 때 순간이동 방지 (최대 0.2초로 보정)
            if dt > 0.5:
                dt = 0.1 

            if basket_pool and hasattr(basket_pool, 'base_speed_mps'):
                baskets = basket_pool.get_all_baskets()
                # 딕셔너리 순회 중 변경 오류 방지를 위해 list로 변환
                for basket_id, basket in list(baskets.items()):
                    if basket['status'] in ['moving', 'in_transit']:
                        line_id = basket.get('line_id')
                        position_m = basket.get('position_m', 0)
                        line_length = basket.get('line_length', 100)
                        
                        if line_id and line_length > 0:
                            # 현재 위치의 속도 계수 가져오기
                            speed_multiplier = get_speed_at_position(line_id, position_m)
                            actual_speed_mps = basket_pool.base_speed_mps * speed_multiplier
                            
                            # dt 동안 이동한 거리 계산
                            distance_delta = actual_speed_mps * dt
                            new_position_m = position_m + distance_delta
                            
                            # ========== 추월 방지: 같은 라인의 앞 바스켓과 최소 거리 유지 ==========
                            # 같은 라인의 다른 바스켓 중 위치가 가까운 것 확인
                            min_distance = 2.0  # 바스켓 간 최소 거리 (미터)
                            is_blocked_by_front = False  # 앞 바스켓에 의해 막혔는가?
                            
                            # (최적화 가능: 라인별로 바스켓 그룹화)
                            for other_id, other_basket in baskets.items():
                                if (other_id != basket_id and 
                                    other_basket.get('line_id') == line_id and
                                    other_basket.get('status') in ['moving', 'in_transit']):
                                    
                                    other_pos = other_basket.get('position_m', 0)
                                    
                                    # 앞 바스켓이 있으면 추월 금지
                                    if other_pos >= position_m and (other_pos - new_position_m) < min_distance:
                                        new_position_m = other_pos - min_distance
                                        # 새 위치가 현재 위치보다 작으면 이동 중지 (병목)
                                        if new_position_m <= position_m:
                                            new_position_m = position_m
                                            is_blocked_by_front = True
                            
                            # 라인 끝에 도달하면 arrived 상태로 변경
                            if new_position_m >= line_length:
                                new_position_m = line_length
                                basket_pool.update_basket_status(basket_id, 'arrived')
                            
                            # 위치 업데이트 및 병목 플래그 설정
                            progress_percent = (new_position_m / line_length * 100) if line_length > 0 else 0
                            basket_pool.update_basket_position(
                                basket_id=basket_id,
                                position_m=new_position_m,
                                progress_percent=min(progress_percent, 100)
                            )
                            
                            # 앞 바스켓 때문에 이동이 멈춘 경우 병목으로 표시
                            if is_blocked_by_front:
                                basket_pool.set_motion_state(basket_id, "stopped", is_bottleneck=True)
                            else:
                                basket_pool.set_motion_state(basket_id, "moving", is_bottleneck=False)
        except Exception as e:
            print(f"[위치 업데이트] 오류 발생: {e}")
            await asyncio.sleep(1)
            last_time = time.time()

async def deployment_queue_task():
    """
    백그라운드 작업: 투입 대기 큐를 처리하여 바스켓을 순차적으로 투입
    
    투입 규칙:
    1. 라인에 바스켓이 없으면 → 즉시 투입
    2. 라인에 바스켓이 있고 + 마지막 투입 후 0.8초 경과 → 투입 가능
    3. 그 외 → 대기
    
    목적: 같은 라인에서 바스켓 간 충돌 방지 및 안전한 간격 유지
    """
    print("[Deployment Queue] 바스켓 투입 시스템 가동")
    global deployment_queue, line_last_deployment
    
    while True:
        try:
            await asyncio.sleep(0.1)  # 100ms마다 체크
            
            if not deployment_queue or not basket_pool:
                continue
            
            current_time = time.time()
            deployed_indices = []  # 투입 완료된 큐 인덱스
            
            for idx, deployment in enumerate(deployment_queue):
                basket_id = deployment["basket_id"]
                zone_id = deployment["zone_id"]
                line_id = deployment["line_id"]
                destination = deployment["destination"]
                
                # 라인별 마지막 투입 시간 체크
                last_deploy_time = line_last_deployment.get(line_id, 0)
                time_since_last = current_time - last_deploy_time
                
                # 해당 라인의 현재 바스켓 수 체크
                line_baskets = [b for b in basket_pool.get_all_baskets().values() 
                              if b.get('line_id') == line_id and b['status'] in ['moving', 'in_transit', 'deploying']]
                
                # 투입 조건 확인
                can_deploy = False
                reason = ""
                
                if len(line_baskets) == 0:
                    # 라인에 바스켓이 없으면 즉시 투입 가능
                    can_deploy = True
                    reason = "라인 비어있음"
                elif time_since_last >= MIN_BASKET_INTERVAL:
                    # 최소 간격이 지났으면 투입 가능
                    can_deploy = True
                    reason = f"간격 충족 ({time_since_last:.1f}s)"
                else:
                    reason = f"대기 중 ({MIN_BASKET_INTERVAL - time_since_last:.1f}s 남음)"
                
                if can_deploy:
                    # 바스켓 투입 실행
                    assigned = basket_pool.assign_basket(basket_id, zone_id, line_id, destination)
                    if assigned:
                        line_last_deployment[line_id] = current_time
                        deployed_indices.append(idx)
                        print(f"[투입 완료] {basket_id} → {line_id} ({reason})")
            
            # 투입 완료된 항목을 큐에서 제거 (역순으로 제거)
            for idx in reversed(deployed_indices):
                deployment_queue.pop(idx)
                
        except Exception as e:
            print(f"[Deployment Queue] 오류: {e}")
            await asyncio.sleep(1)

async def recycle_baskets_task():
    """
    백그라운드 작업: 도착(arrived)한 바스켓을 주기적으로 회수하여 재사용 가능하게 만듦
    
    동작:
    - 5초마다 모든 바스켓 상태 확인
    - arrived 상태인 바스켓을 available 상태로 전환
    - 바스켓 풀에서 재사용 가능하도록 리셋
    """
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
    """서버 시작 시 EventHub Consumer 시작"""
    global consumer, deployment_queue, line_last_deployment
    deployment_queue = []
    line_last_deployment = {}
    
    try:
        init_data_db()  # 데이터베이스 초기화
        print("[STARTUP] ✅ 데이터베이스 초기화 완료")
        
        # BasketPool 초기화
        db = next(data_db())
        try:
            initialize_basket_pool(db)
            
            # zones 정보 조회
            zones = logis_data_db.get_all_zones(db)
            print(f"[STARTUP] ✅ BasketPool 초기화 완료, {len(zones)}개 존 로드")
            
            # 센서-라인 매핑 생성 (센서 위치 정보)
            sensor_line_mapping = {}
            for zone in zones:
                zone_lines = zone.zone_lines if zone.zone_lines else []
                for line in zone_lines:
                    line_length = line.length if hasattr(line, 'length') else 100
                    # 라인의 센서 개수 추정 (zone.sensors를 라인 수로 나눔)
                    total_zone_sensors = zone.sensors if zone.sensors else 0
                    sensors_per_line = max(1, int(total_zone_sensors / len(zone_lines))) if len(zone_lines) > 0 else 0
                    
                    # 각 센서의 위치 계산
                    for i in range(sensors_per_line):
                        sensor_num = i + 1
                        sensor_id = f"{line.line_id}-S{sensor_num:03d}"
                        position_m = (sensor_num / (sensors_per_line + 1)) * line_length
                        sensor_line_mapping[sensor_id] = {
                            "line_id": line.line_id,
                            "position_m": position_m,
                            "line_length": line_length
                        }
            
            print(f"[STARTUP] ✅ 센서-라인 매핑 생성 완료: {len(sensor_line_mapping)}개 센서")
            
        finally:
            db.close()
        
        # EventHub Consumer 시작 (basket_pool 참조 전달)
        if os.getenv("EVENTHUB_CONNECTION_STRING"):
            try:
                from eventhub_consumer import SensorEventConsumer
                consumer = SensorEventConsumer(
                    basket_pool=basket_pool,
                    sensor_line_mapping=sensor_line_mapping
                )
                consumer.start()
                print("[STARTUP] ✅ EventHub Consumer 시작 완료 (basket_pool 연동)")
            except Exception as e:
                print(f"[STARTUP] ⚠️ EventHub Consumer 시작 실패: {e}")
        else:
            print("[STARTUP] ⚠️ EventHub Consumer 비활성화 상태 - Event Hub 연동 없음")
        
        print("[STARTUP] ✅ Backend 서버 시작 완료")
        
        # 백그라운드 태스크들 시작
        asyncio.create_task(deployment_queue_task())  # 투입 큐 처리
        asyncio.create_task(recycle_baskets_task())  # 바스켓 회수
        asyncio.create_task(update_basket_positions_task())  # 위치 업데이트
        
    except Exception as e:
        print(f"[STARTUP] ❌ 서버 시작 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise

@app.get("/health")
async def health_check():
    """기본 헬스 체크"""
    return {
        "status": "ok",
        "service": "backend",
        "events_received": consumer.get_event_count() if consumer else 0
    }

@app.get("/debug/eventhub-messages")
async def get_eventhub_messages(limit: int = 100):
    """최근 EventHub 메시지 조회 (디버그용)"""
    if not consumer:
        return {"messages": [], "count": 0, "error": "Consumer not initialized"}
    
    # 최근 메시지를 역순으로 (최신순)
    recent_messages = consumer.latest_events[-limit:][::-1]
    
    return {
        "count": len(recent_messages),
        "total_received": len(consumer.latest_events),
        "limit": limit,
        "messages": recent_messages
    }

@app.get("/debug/eventhub-stats")
async def get_eventhub_stats():
    """EventHub 메시지 수신 통계"""
    if not consumer:
        return {"error": "Consumer not initialized"}
    
    # 구역별 메시지 수 계산
    zone_stats = {}
    for event in consumer.latest_events:
        zone_id = event.get("zone_id", "unknown")
        if zone_id not in zone_stats:
            zone_stats[zone_id] = {"total": 0, "signal_true": 0}
        zone_stats[zone_id]["total"] += 1
        if event.get("signal"):
            zone_stats[zone_id]["signal_true"] += 1
    
    return {
        "total_messages": len(consumer.latest_events),
        "zone_stats": zone_stats,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health/db")
async def health_check_db():
    """데이터베이스 연결 상태 확인"""
    from database import engine
    import os
    
    az_url = os.getenv("AZ_POSTGRE_DATABASE_URL")
    db_url = os.getenv("DATABASE_URL")
    
    try:
        # 현재 연결된 DB 확인
        current_url = str(engine.url)
        
        return {
            "status": "healthy",
            "connected_to": "Azure PostgreSQL" if "psql-logistics-kr" in current_url else "Local PostgreSQL",
            "current_database_url": current_url.split("@")[1] if "@" in current_url else current_url,
            "env_AZ_POSTGRE_DATABASE_URL": "✅ 설정됨" if az_url else "❌ 없음",
            "env_DATABASE_URL": "✅ 설정됨" if db_url else "❌ 없음"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/health/consumer")
async def health_check_consumer():
    """EventHub Consumer 상태 확인"""
    if consumer is None:
        return {
            "status": "disabled",
            "message": "EventHub Consumer가 비활성화되어 있습니다"
        }
    
    return {
        "status": "enabled",
        "is_running": consumer.is_running if hasattr(consumer, 'is_running') else "unknown",
        "latest_events_count": len(consumer.latest_events) if hasattr(consumer, 'latest_events') else 0,
        "buffer_size": len(consumer.event_buffer) if hasattr(consumer, 'event_buffer') else 0,
        "message": "EventHub Consumer가 활성화되어 있습니다"
    }

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 EventHub Consumer 중지"""
    try:
        if consumer:
            consumer.stop()
            print("[SHUTDOWN] EventHub Consumer 중지 완료")
    except Exception as e:
        print(f"[SHUTDOWN] 오류: {e}")
    
    print("[SHUTDOWN] Backend 서버 종료")

@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "status": "ok",
        "message": "Azure Rail Logistics Backend",
        "events_received": consumer.get_event_count() if consumer else 0
    }

@app.get("/events/latest")
async def get_latest_events(count: int = 10, only_active: bool = False):
    """최근 센서 이벤트 조회"""
    # consumer.latest_events 리스트를 직접 사용하여 안전하게 조회
    if consumer and hasattr(consumer, 'latest_events') and consumer.latest_events:
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
    if not consumer or not hasattr(consumer, 'latest_events'):
        return {"message": "No consumer available"}
    
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
    """
    존별 요약 정보
    
    포함 사항:
    - 총 바스켓 수, in_transit 바스켓 수
    - 병목 상태인 바스켓 개수
    - 센서 데이터 기반 정보 (EventHub 활성화 시)
    """
    zone_data = {}
    
    # ========== 방법 1: 바스켓 풀 상태 기반 정보 ==========
    if basket_pool:
        baskets = basket_pool.get_all_baskets()
        for basket_id, basket in baskets.items():
            zone_id = basket.get('zone_id')
            if not zone_id:
                continue
            
            if zone_id not in zone_data:
                zone_data[zone_id] = {
                    "zone_id": zone_id,
                    "total_baskets": 0,
                    "in_transit_baskets": 0,
                    "bottleneck_count": 0,
                    "arrived_baskets": 0,
                    "data_points": 0,
                    "total_throughput": 0,
                    "total_speed": 0,
                    "speed_count": 0
                }
            
            zone_data[zone_id]["total_baskets"] += 1
            
            if basket['status'] in ['in_transit', 'moving']:
                zone_data[zone_id]["in_transit_baskets"] += 1
            
            if basket['status'] == 'arrived':
                zone_data[zone_id]["arrived_baskets"] += 1
            
            if basket.get('is_bottleneck') == True:
                zone_data[zone_id]["bottleneck_count"] += 1
    
    # ========== 방법 2: EventHub 센서 데이터 기반 정보 (옵션) ==========
    if consumer and hasattr(consumer, 'latest_events'):
        events = consumer.latest_events
        if events:
            for event in events:
                zone_id = event.get("zone_id")
                if not zone_id:
                    continue
                
                if zone_id not in zone_data:
                    zone_data[zone_id] = {
                        "zone_id": zone_id,
                        "total_baskets": 0,
                        "in_transit_baskets": 0,
                        "bottleneck_count": 0,
                        "arrived_baskets": 0,
                        "data_points": 0,
                        "total_throughput": 0,
                        "total_speed": 0,
                        "speed_count": 0
                    }
                
                zone_data[zone_id]["data_points"] += 1
                
                if event.get("signal"):
                    zone_data[zone_id]["total_throughput"] += 1
                    speed = event.get("speed", 0)
                    if speed > 0:
                        zone_data[zone_id]["total_speed"] += speed
                        zone_data[zone_id]["speed_count"] += 1
    
    # 평균 계산 및 결과 생성
    result = []
    for zone_id, data in zone_data.items():
        avg_speed = data["total_speed"] / data["speed_count"] if data["speed_count"] > 0 else 0
        result.append({
            "zone_id": zone_id,
            "total_baskets": data["total_baskets"],
            "in_transit_baskets": data["in_transit_baskets"],
            "arrived_baskets": data["arrived_baskets"],
            "bottleneck_count": data["bottleneck_count"],
            "data_points": data["data_points"],
            "total_throughput": data["total_throughput"],
            "avg_speed": round(avg_speed, 2)
        })
    
    return result

@app.get("/bottlenecks")
async def get_bottlenecks():
    """
    병목 현상 감지 - 바스켓 상태 기반
    
    병목 판정:
    - is_bottleneck == True인 바스켓 (앞 바스켓 때문에 이동 중단)
    - 또는 센서 데이터에서 signal==true && speed<30 이벤트
    """
    bottleneck_zones = {}
    
    # ========== 방법 1: 바스켓 풀 상태 기반 병목 감지 ==========
    if basket_pool:
        baskets = basket_pool.get_all_baskets()
        for basket_id, basket in baskets.items():
            # is_bottleneck이 true인 바스켓 찾기
            if basket.get('is_bottleneck') == True:
                zone_id = basket.get('zone_id')
                if zone_id:
                    if zone_id not in bottleneck_zones:
                        bottleneck_zones[zone_id] = {
                            "zone_id": zone_id,
                            "aggregated_id": f"BOTTLENECK-{zone_id}",
                            "bottleneck_count": 0,
                            "bottleneck_baskets": []
                        }
                    bottleneck_zones[zone_id]["bottleneck_count"] += 1
                    bottleneck_zones[zone_id]["bottleneck_baskets"].append(basket_id)
    
    # ========== 방법 2: EventHub 센서 데이터 기반 병목 감지 (옵션) ==========
    if consumer and hasattr(consumer, 'latest_events'):
        events = consumer.latest_events
        if events:
            bottleneck_events = [e for e in events if e.get("signal") == True and e.get("speed", 100) < 30]
            for event in bottleneck_events:
                zone_id = event.get("zone_id")
                if zone_id:
                    if zone_id not in bottleneck_zones:
                        bottleneck_zones[zone_id] = {
                            "zone_id": zone_id,
                            "aggregated_id": f"BOTTLENECK-{zone_id}",
                            "bottleneck_count": 0,
                            "bottleneck_baskets": []
                        }
                    # 센서 데이터 기반 병목은 카운트하지만 바스켓 리스트에는 추가하지 않음
                    bottleneck_zones[zone_id]["sensor_event_count"] = bottleneck_zones[zone_id].get("sensor_event_count", 0) + 1
    
    # 병목 바스켓 개수로 정렬
    result = sorted(bottleneck_zones.values(), key=lambda x: x["bottleneck_count"], reverse=True)
    return result

@app.get("/sensors/history")
async def get_sensor_history(zone_id: Optional[str] = None, count: int = 100):
    """센서 히스토리 조회 - 원본 센서 데이터 반환 (집계 X)"""
    if not consumer or not hasattr(consumer, 'latest_events'):
        return []
    
    events = consumer.latest_events
    
    # zone_id로 필터링
    if zone_id:
        filtered_events = [e for e in events if e.get("zone_id") == zone_id]
    else:
        filtered_events = events
    
    # 최근 count개만 반환
    return filtered_events[-count:]

@app.get("/api/sensor-events/db")
async def get_sensor_events_from_db(
    zone_id: Optional[str] = None,
    basket_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(data_db)
):
    """
    데이터베이스에 저장된 센서 이벤트 조회 (분석/히스토리용)
    
    Args:
        zone_id: 구획 ID (선택)
        basket_id: 바스켓 ID (선택)
        limit: 반환 행 수 (기본 100)
        offset: 시작 위치 (기본 0, 페이지네이션용)
    
    Returns:
        sensor_events 테이블의 데이터
    """
    from models import SensorEvent
    from datetime import datetime, timedelta
    
    try:
        query = db.query(SensorEvent)
        
        # 필터링
        if zone_id:
            query = query.filter(SensorEvent.zone_id == zone_id)
        if basket_id:
            query = query.filter(SensorEvent.basket_id == basket_id)
        
        # 정렬 및 페이지네이션
        query = query.order_by(SensorEvent.timestamp.desc())
        total_count = query.count()
        
        events = query.offset(offset).limit(limit).all()
        
        # 결과 변환
        result = [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "zone_id": e.zone_id,
                "basket_id": e.basket_id,
                "sensor_id": e.sensor_id,
                "signal": e.signal,
                "speed": e.speed,
                "position_x": e.position_x
            }
            for e in events
        ]
        
        return {
            "total_count": total_count,
            "returned_count": len(result),
            "offset": offset,
            "limit": limit,
            "events": result
        }
        
    except Exception as e:
        print(f"[API] DB 조회 오류: {e}")
        return {
            "error": str(e),
            "events": []
        }

@app.get("/api/sensor-events/stats")
async def get_sensor_events_stats(
    zone_id: Optional[str] = None,
    hours: int = 1,
    db: Session = Depends(data_db)
):
    """
    센서 이벤트 통계 (최근 N시간)
    
    Args:
        zone_id: 구획 ID (선택)
        hours: 조회 기간 (기본 1시간)
    
    Returns:
        - 총 이벤트 수
        - 신호 감지 횟수
        - 평균 속도
        - 구획별 통계
    """
    from models import SensorEvent
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = db.query(SensorEvent).filter(SensorEvent.timestamp >= cutoff_time)
        
        if zone_id:
            query = query.filter(SensorEvent.zone_id == zone_id)
        
        # 전체 통계
        total = query.count()
        signal_count = query.filter(SensorEvent.signal == True).count()
        
        avg_speed = db.query(func.avg(SensorEvent.speed)).filter(
            SensorEvent.timestamp >= cutoff_time,
            SensorEvent.speed > 0
        )
        if zone_id:
            avg_speed = avg_speed.filter(SensorEvent.zone_id == zone_id)
        avg_speed = float(avg_speed.scalar() or 0)
        
        # 구획별 통계
        zone_stats = db.query(
            SensorEvent.zone_id,
            func.count(SensorEvent.id).label('count'),
            func.sum((SensorEvent.signal == True).cast(Integer)).label('signal_count'),
            func.avg(SensorEvent.speed).label('avg_speed')
        ).filter(
            SensorEvent.timestamp >= cutoff_time
        ).group_by(SensorEvent.zone_id).all()
        
        zone_summary = [
            {
                "zone_id": z[0],
                "event_count": z[1],
                "signal_count": z[2] or 0,
                "avg_speed": round(float(z[3] or 0), 2)
            }
            for z in zone_stats
        ]
        
        return {
            "period_hours": hours,
            "total_events": total,
            "signal_detected": signal_count,
            "avg_speed": round(avg_speed, 2),
            "zones": zone_summary
        }
        
    except Exception as e:
        print(f"[API] 통계 조회 오류: {e}")
        return {
            "error": str(e)
        }

# ============ ZONES 설정 API ============

@app.get("/zones")
async def get_zones(db: Session = Depends(data_db)):
    """
    모든 존 정보 조회 (라인 용량 정보 포함)
    
    Returns:
        - zones: 존 목록
        - line_capacities: 각 라인의 최대 수용량 및 현재 사용량
    """
    zones = logis_data_db.get_all_zones(db)
    print(f"[API] /zones 반환: {len(zones)}개 존")
    
    # 라인 용량 정보 추가 (현재 사용량 포함)
    enriched_line_capacities = {}
    if basket_pool and line_capacity_info:
        for line_id, capacity_info in line_capacity_info.items():
            # 현재 해당 라인에 있는 바스켓 수 계산
            current_baskets = [b for b in basket_pool.get_all_baskets().values() 
                             if b.get('line_id') == line_id and b['status'] in ['moving', 'in_transit', 'deploying']]
            current_count = len(current_baskets)
            max_capacity = capacity_info["max"]
            
            enriched_line_capacities[line_id] = {
                "current": current_count,
                "max": max_capacity,
                "length": capacity_info["length"],
                "percent": (current_count / max_capacity * 100) if max_capacity > 0 else 0
            }
    
    if zones:
        print(f"  첫번째 존: {zones[0]}")
    
    return {
        "zones": zones,
        "line_capacities": enriched_line_capacities
    }

@app.post("/zones")
async def create_zone(zone: LogisticsZoneCreate, db: Session = Depends(data_db)):
    """새 존 생성 (존 정보만, 라인은 별도로)"""
    return logis_data_db.save_zone(db, zone)

@app.post("/lines")
async def create_lines(lines: List[dict], db: Session = Depends(data_db)):
    """라인 저장 (배치)"""
    return logis_data_db.save_lines(db, lines)

def _create_or_update_zones_and_lines(db: Session, zones_list: List[LogisticsZoneCreate]) -> tuple:
    """
    존과 라인을 일괄 생성 또는 업데이트 (중복 코드 제거용 분리 함수)
    
    Args:
        db: Database session
        zones_list: 생성/업데이트할 존 목록
    
    Returns:
        (생성된 존 개수, 생성된 라인 개수)
    """
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

    zones_created = 0
    lines_created = 0

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
            zones_created += 1
        
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
        lines_created += len(new_lines)
        print(f"    - Zone {zone_data.zone_id}: 새 라인 {len(new_lines)}개 생성됨")
    
    return zones_created, lines_created

@app.get("/zones/config", response_model=List[LogisticsZoneSchema])
async def get_zones_config(db: Session = Depends(data_db)):
    """현재 zones 설정 조회"""
    zones = logis_data_db.get_all_zones(db)
    return zones

@app.post("/zones/config", response_model=LogisticsZoneSchema)
async def create_zone_with_lines(zone: LogisticsZoneCreate, db: Session = Depends(data_db)):
    """새 zone 추가 (라인도 자동 생성)"""
    return logis_data_db.save_zone(db, zone)

@app.put("/zones/config/{zone_id}", response_model=LogisticsZoneSchema)
async def update_zone(zone_id: str, zone: LogisticsZoneCreate, db: Session = Depends(data_db)):
    """zone 업데이트"""
    db_zone = logis_data_db.update_zone(db, zone_id, zone)
    if not db_zone:
        return {"error": "Zone not found"}
    return db_zone

@app.delete("/zones/config/{zone_id}")
async def delete_zone(zone_id: str, db: Session = Depends(data_db)):
    """zone 삭제"""
    result = logis_data_db.delete_zone(db, zone_id)
    if not result:
        return {"error": "Zone not found"}
    return {"deleted": result}

@app.post("/zones/config/batch")
async def set_zones_batch(zones_list: List[LogisticsZoneCreate], db: Session = Depends(data_db)):
    """zones 전체 설정 (기존 데이터 전부 교체) - SQLite + Azure 동시 저장"""
    print(f"\n[API] /zones/config/batch 요청 수신 (프리셋 저장)")
    print(f"  - 수신된 존 개수: {len(zones_list)}")
    for i, zone in enumerate(zones_list):
        print(f"    [{i+1}] {zone.zone_id} ({zone.name}): Lines={zone.lines}, Sensors={zone.sensors}")
        
    try:
        # 분리 함수 사용: 존/라인 생성 로직 통합
        zones_created, lines_created = _create_or_update_zones_and_lines(db, zones_list)
        
        db.commit()
        print("  ✅ 로컬 PostgreSQL 저장 완료")
        
        # ====== SQLite + Azure 동시 저장 (백그라운드) ======
        threading.Thread(
            target=_sync_zones_to_sqlite_and_azure,
            args=(zones_list,),
            daemon=True
        ).start()
        
        return db.query(LogisticsZone).all()
        
    except Exception as e:
        db.rollback()
        print(f"  - 배치 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"존/라인 저장 실패: {str(e)}"
            }
        )



def _sync_zones_to_sqlite_and_azure(zones_list: List[LogisticsZoneCreate]):
    """로컬 SQLite + Azure PostgreSQL에 동시에 동기화"""
    try:
        # ===== 로컬 SQLite 저장 =====
        _save_zones_to_sqlite(zones_list)
        
        # ===== Azure PostgreSQL 저장 =====
        if AzureSession:
            _save_zones_to_azure(zones_list)
        else:
            print("  ⚠️ Azure 저장 스킵: AZ_POSTGRE_DATABASE_URL 미설정")
            
    except Exception as e:
        print(f"  ❌ SQLite/Azure 동기화 실패: {e}")


def _save_zones_to_sqlite(zones_list: List[LogisticsZoneCreate]):
    """로컬 SQLite에 zones 저장"""
    from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, Index
    from sqlalchemy.orm import declarative_base
    from sqlalchemy.sql import func
    
    BaseSQLite = declarative_base()
    
    class SQLiteZone(BaseSQLite):
        __tablename__ = 'logistics_zones'
        zone_id = Column(String(50), primary_key=True)
        name = Column(String(100), nullable=False)
        lines = Column(Integer, nullable=False)
        length = Column(Integer, nullable=False)
        sensors = Column(Integer, nullable=False)
        created_at = Column(TIMESTAMP, default=func.now())
    
    class SQLiteLine(BaseSQLite):
        __tablename__ = 'logistics_lines'
        line_id = Column(String(50), primary_key=True)
        zone_id = Column(String(50), ForeignKey('logistics_zones.zone_id'), nullable=False)
        length = Column(Integer, nullable=False)
        sensors = Column(Integer, nullable=False)
    
    BaseSQLite.metadata.create_all(local_sqlite_engine)
    
    sqlite_session = LocalSQLiteSession()
    try:
        # 기존 데이터 삭제
        sqlite_session.execute(delete(SQLiteLine))
        sqlite_session.execute(delete(SQLiteZone))
        sqlite_session.commit()
        
        # 새 데이터 삽입
        for zone_data in zones_list:
            zone = SQLiteZone(
                zone_id=zone_data.zone_id,
                name=zone_data.name,
                lines=zone_data.lines,
                length=zone_data.length,
                sensors=zone_data.sensors
            )
            sqlite_session.add(zone)
            
            sensors_per_line = zone_data.sensors // zone_data.lines if zone_data.lines > 0 else 0
            for i in range(zone_data.lines):
                line_id = f"{zone_data.zone_id}-{i+1:03d}"
                line = SQLiteLine(
                    line_id=line_id,
                    zone_id=zone_data.zone_id,
                    length=zone_data.length,
                    sensors=sensors_per_line
                )
                sqlite_session.add(line)
        
        sqlite_session.commit()
        print("  ✅ SQLite 저장 완료")
        
    except Exception as e:
        sqlite_session.rollback()
        print(f"  ❌ SQLite 저장 실패: {e}")
    finally:
        sqlite_session.close()


def _save_zones_to_azure(zones_list: List[LogisticsZoneCreate]):
    """Azure PostgreSQL에 zones 저장"""
    if not AzureSession:
        return
    
    azure_session = AzureSession()
    try:
        # 기존 데이터 삭제 (안전한 방식)
        azure_session.execute(delete(LogisticsLine))
        azure_session.execute(delete(LogisticsZone))
        azure_session.commit()
        
        # 새 데이터 삽입
        for zone_data in zones_list:
            zone = LogisticsZone(
                zone_id=zone_data.zone_id,
                name=zone_data.name,
                lines=zone_data.lines,
                length=zone_data.length,
                sensors=zone_data.sensors
            )
            azure_session.add(zone)
            
            sensors_per_line = zone_data.sensors // zone_data.lines if zone_data.lines > 0 else 0
            for i in range(zone_data.lines):
                line_id = f"{zone_data.zone_id}-{i+1:03d}"
                line = LogisticsLine(
                    zone_id=zone_data.zone_id,
                    line_id=line_id,
                    length=zone_data.length,
                    sensors=sensors_per_line
                )
                azure_session.add(line)
        
        azure_session.commit()
        print("  ✅ Azure PostgreSQL 저장 완료")
        
    except Exception as e:
        azure_session.rollback()
        print(f"  ❌ Azure PostgreSQL 저장 실패: {e}")
    finally:
        azure_session.close()

@app.post("/api/baskets/create")
async def create_baskets(
    request_data: BasketCreateRequest,
    db: Session = Depends(data_db)
):
    """
    바스켓 생성 및 라인에 할당 (수정됨: 중복 코드 제거 완료)
    
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
    
    # ============ 라인별 현재 용량 체크 (저장된 용량 정보 사용) ============
    warnings = []
    line_capacities = {}
    for line_id in target_lines:
        # 초기화 시 계산된 용량 정보 사용 (매번 재계산 방지)
        capacity_info = line_capacity_info.get(line_id, {"max": 20, "length": 100})
        max_capacity = capacity_info["max"]
        
        # 현재 해당 라인에 있는 바스켓 수 계산
        current_baskets = [b for b in basket_pool.get_all_baskets().values() 
                         if b.get('line_id') == line_id and b['status'] in ['moving', 'in_transit', 'deploying']]
        current_count = len(current_baskets)
        capacity_percent = (current_count / max_capacity * 100) if max_capacity > 0 else 0
        
        line_capacities[line_id] = {
            "current": current_count,
            "max": max_capacity,
            "length": capacity_info["length"],
            "percent": capacity_percent
        }
        
        # 80% 이상 사용 중이면 경고 메시지 추가
        if capacity_percent >= MAX_LINE_CAPACITY_PERCENT:
            warnings.append(f"⚠️ {line_id} 라인 혼잡 ({capacity_percent:.0f}% 사용 중)")
    
    # 투입 큐에 추가 (즉시 투입하지 않고 큐에 넣음)
    queued_baskets = []
    destination = request_data.destination or request_data.zone_id
    
    for i in range(request_data.count):
        if i >= len(available_baskets):
            break
            
        basket = available_baskets[i]
        basket_id = basket["basket_id"]
        
        # 라인 선택: 용량이 적은 라인 우선 (로드 밸런싱)
        if request_data.line_id:
            selected_line_id = request_data.line_id
        else:
            # 용량 퍼센트가 낮은 라인부터 선택
            sorted_lines = sorted(target_lines, key=lambda lid: line_capacities.get(lid, {}).get("percent", 0))
            selected_line_id = sorted_lines[i % len(sorted_lines)]
        
        # 투입 큐에 추가 (상태를 deploying으로 변경)
        basket_pool.update_basket_status(basket_id, 'deploying')
        deployment_queue.append({
            "basket_id": basket_id,
            "zone_id": request_data.zone_id,
            "line_id": selected_line_id,
            "destination": destination
        })
        
        queued_baskets.append({
            "basket_id": basket_id,
            "line_id": selected_line_id,
            "status": "deploying"
        })
        print(f"[투입 큐 추가] {basket_id} → {selected_line_id} (대기열: {len(deployment_queue)})")
    
    return {
        "success": True,
        "queued_count": len(queued_baskets),
        "baskets": queued_baskets,
        "queue_length": len(deployment_queue),
        "line_capacities": line_capacities,
        "warnings": warnings,
        "message": f"{len(queued_baskets)}개 바스켓이 투입 대기열에 추가되었습니다. 순차적으로 투입됩니다."
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
        
        # 실시간 위치 정보: EventHub를 통해 수신되는 센서 데이터로 업데이트됨
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
    """현재 이동 중인 바스켓들의 실시간 위치 정보 (EventHub를 통해 수신되는 센서 데이터)"""
    return []

# ============ EventHub Consumer 상태 API ============

@app.get("/simulator/status")
async def get_consumer_status():
    """EventHub Consumer 상태 조회 및 라인별 속도 구간 정보 제공"""
    latest_time = None
    events_count = 0
    if consumer and hasattr(consumer, 'latest_events') and consumer.latest_events:
        events_count = len(consumer.latest_events)
        if events_count > 0:
            latest_time = consumer.latest_events[-1].get("timestamp")

    # 라인별 속도 구간 정보 추가
    line_speed_zones = {}
    if basket_pool and hasattr(basket_pool, 'line_speed_zones'):
        line_speed_zones = basket_pool.line_speed_zones

    return {
        "running": consumer.is_running if consumer and hasattr(consumer, 'is_running') else False,
        "events_received": events_count,
        "latest_event_time": latest_time,
        "adapter_type": "EventHub Consumer Only",
        "message": "센서 데이터는 logistics-sensor-simulator 모듈에서 IoT Hub로 전송됩니다",
        "line_speed_zones": line_speed_zones  # 구간별 속도 정보 추가
    }

@app.post("/simulator/start")
async def start_simulator():
    """
    시뮬레이터 시작 - 센서 시뮬레이터 컨테이너의 API 호출
    """
    print("[Simulator Control] 🔵 /simulator/start 요청 수신")
    try:
        import httpx
        print(f"[Simulator Control] {SIMULATOR_API_BASE}로 센서 시뮬레이터 시작 요청 중...")
        async with httpx.AsyncClient(timeout=SIMULATOR_API_TIMEOUT) as client:
            # localhost로 접근 (두 컨테이너 모두 host network 사용)
            response = await client.post(f"{SIMULATOR_API_BASE}/simulator/start")
            print(f"[Simulator Control] 응답 상태: {response.status_code}")
            result = response.json()
            print(f"[Simulator Control] ✅ 시작 완료: {result}")
            return result
    except Exception as e:
        print(f"[Simulator Control] ❌ 시작 실패: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"시뮬레이터 시작 실패: {str(e)}",
                "running": False
            }
        )

@app.post("/simulator/stop")
async def stop_simulator():
    """
    시뮬레이터 정지 - 센서 시뮬레이터 컨테이너의 API 호출
    """
    print("[Simulator Control] 🔴 /simulator/stop 요청 수신")
    try:
        import httpx
        print(f"[Simulator Control] {SIMULATOR_API_BASE}로 센서 시뮬레이터 중지 요청 중...")
        async with httpx.AsyncClient(timeout=SIMULATOR_API_TIMEOUT) as client:
            response = await client.post(f"{SIMULATOR_API_BASE}/simulator/stop")
            print(f"[Simulator Control] 응답 상태: {response.status_code}")
            result = response.json()
            print(f"[Simulator Control] ✅ 중지 완료: {result}")
            return result
    except Exception as e:
        print(f"[Simulator Control] ❌ 중지 실패: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"시뮬레이터 중지 실패: {str(e)}",
                "running": True
            }
        )

@app.post("/simulator/reset")
async def reset_simulator(db: Session = Depends(data_db)):
    """
    시뮬레이터 초기화 - 바스켓 풀과 배포 큐 리셋
    """
    try:
        global basket_pool, deployment_queue
        
        # 바스켓 풀 초기화
        if basket_pool:
            basket_pool.baskets.clear()
            basket_pool._initialize_pool()
            print("[RESET] 바스켓 풀 초기화 완료")
        
        # 배포 큐 초기화
        deployment_queue.clear()
        print("[RESET] 배포 큐 초기화 완료")
        
        return {
            "status": "success",
            "message": "시뮬레이터가 초기화되었습니다.",
            "baskets_total": len(basket_pool.baskets) if basket_pool else 0
        }
    except Exception as e:
        print(f"[Simulator Reset] 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"시뮬레이터 초기화 실패: {str(e)}"
            }
        )

# ============ 프리셋 API (Azure PostgreSQL에서 읽기) ============

@app.get("/presets")
async def get_all_presets(db: Session = Depends(data_db)):
    """사용 가능한 모든 프리셋 목록 조회"""
    try:
        print("[DEBUG] /presets 엔드포인트 호출됨!")
        
        # 직접 SQL로 확인
        presets_count = db.execute(text("SELECT COUNT(*) FROM presets")).scalar()
        print(f"[DEBUG] SQL: presets 테이블 행 개수: {presets_count}")
        
        # ORM으로 조회
        presets = db.query(Preset).all()
        print(f"[DEBUG] ORM: Preset 객체 개수: {len(presets) if presets else 0}")
        
        if presets:
            for p in presets:
                print(f"[DEBUG]   - {p.preset_key}: {p.preset_name}")
        
        if not presets or presets_count == 0:
            print(f"[DEBUG] Preset이 비어있음, 빈 리스트 반환")
            return {"presets": []}
        
        result = []
        for preset in presets:
            zones = db.query(PresetZone).filter(PresetZone.preset_key == preset.preset_key).all()
            total_lines = sum(z.lines for z in zones) if zones else 0
            total_sensors = sum(z.sensors for z in zones) if zones else 0
            
            result.append({
                "preset_key": preset.preset_key,
                "preset_name": preset.preset_name,
                "zones_count": len(zones),
                "total_lines": total_lines,
                "total_sensors": total_sensors,
                "zones": [
                    {
                        "id": z.zone_id,
                        "name": z.zone_name,
                        "lines": z.lines,
                        "length": z.length,
                        "sensors": z.sensors
                    } for z in zones
                ]
            })
        
        print(f"[DEBUG] 최종 결과: {len(result)}개 프리셋 반환")
        return {"presets": result}
        
    except Exception as e:
        print(f"❌ 프리셋 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"프리셋 조회 실패: {str(e)}"
            }
        )

@app.post("/presets/{preset_key}/apply")
async def apply_preset(preset_key: str, db: Session = Depends(data_db)):
    """프리셋 적용 - 선택한 프리셋의 모든 존/라인을 현재 설정으로 로드"""
    global basket_pool
    
    try:
        # 1. 프리셋 조회
        preset = db.query(Preset).filter(Preset.preset_key == preset_key).first()
        if not preset:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"프리셋 '{preset_key}'을 찾을 수 없습니다"
                }
            )
        
        # 2. 프리셋 존 조회
        preset_zones = db.query(PresetZone).filter(PresetZone.preset_key == preset_key).all()
        if not preset_zones:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"프리셋 '{preset_key}'에 존이 없습니다"
                }
            )
        
        # 3. PresetZone을 LogisticsZoneCreate로 변환
        zones_to_apply = [
            LogisticsZoneCreate(
                zone_id=pz.zone_id,
                name=pz.zone_name,
                lines=pz.lines,
                length=pz.length,
                sensors=pz.sensors
            )
            for pz in preset_zones
        ]
        
        # 4. 분리 함수 사용: 존/라인 생성 로직 통합
        zones_created, lines_created = _create_or_update_zones_and_lines(db, zones_to_apply)
        sensors_created = sum(z.sensors for z in zones_to_apply)
        
        db.commit()
        
        # 5. BasketPool 재초기화
        initialize_basket_pool(db)
        
        print(f"✅ 프리셋 '{preset_key}' 적용 완료: {len(zones_to_apply)}개 존 로드됨")
        
        return {
            "status": "success",
            "preset_key": preset_key,
            "preset_name": preset.preset_name,
            "zones_loaded": len(zones_to_apply),
            "zones_created": zones_created,
            "lines_created": lines_created,
            "sensors_created": sensors_created,
            "message": f"프리셋 '{preset.preset_name}'이 적용되었습니다"
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ 프리셋 적용 실패: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"프리셋 적용 실패: {str(e)}"
            }
        )

# ============ Mock 센서 데이터 (테스트용) ============
@app.post("/test/mock-sensor-event")
async def mock_sensor_event(
    zone_id: str,
    signal: bool = True,
    speed: int = 50
):
    """
    테스트용: Mock 센서 이벤트를 EventHub Consumer의 latest_events에 추가
    
    실제 센서 데이터가 없을 때 병목 감지 테스트용
    
    Example: POST /test/mock-sensor-event?zone_id=01-PK&signal=true&speed=25
    """
    if not consumer:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "EventHub Consumer가 활성화되지 않았습니다"
            }
        )
    
    event_data = {
        "timestamp": datetime.now().isoformat(),
        "zone_id": zone_id,
        "signal": signal,
        "speed": speed
    }
    
    # EventHub Consumer의 latest_events에 직접 추가
    consumer.latest_events.append(event_data)
    if len(consumer.latest_events) > consumer.max_events:
        consumer.latest_events.pop(0)
    
    print(f"[MOCK] Mock 센서 이벤트 추가: zone_id={zone_id}, signal={signal}, speed={speed}")
    
    return {
        "status": "success",
        "message": f"Mock 이벤트 추가됨: {event_data}",
        "total_events": len(consumer.latest_events)
    }

@app.post("/test/mock-sensor-burst")
async def mock_sensor_burst(
    zone_id: str,
    count: int = 10,
    signal: bool = True,
    speed: int = 25
):
    """
    테스트용: 다수의 Mock 센서 이벤트를 한번에 추가 (병목 감지 테스트)
    
    Example: POST /test/mock-sensor-burst?zone_id=01-PK&count=50&speed=20
    """
    if not consumer:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "EventHub Consumer가 활성화되지 않았습니다"
            }
        )
    
    added_count = 0
    for i in range(count):
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "zone_id": zone_id,
            "signal": signal,
            "speed": speed,
            "sequence": i + 1
        }
        
        consumer.latest_events.append(event_data)
        if len(consumer.latest_events) > consumer.max_events:
            consumer.latest_events.pop(0)
        added_count += 1
    
    print(f"[MOCK] Mock 센서 burst 완료: {added_count}개 이벤트 추가 (zone_id={zone_id}, speed={speed})")
    
    return {
        "status": "success",
        "message": f"Mock 이벤트 {added_count}개 추가됨",
        "total_events": len(consumer.latest_events),
        "zone_id": zone_id,
        "speed": speed,
        "signal": signal
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)