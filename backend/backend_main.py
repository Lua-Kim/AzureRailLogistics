from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kafka_consumer import SensorEventConsumer

app = FastAPI(title="Azure Rail Logistics Backend")

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

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 Kafka Consumer 시작"""
    consumer.start()
    print("Backend 서버 시작 완료")

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 Kafka Consumer 중지"""
    consumer.stop()
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
