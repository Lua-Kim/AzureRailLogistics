from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, text
from datetime import datetime, timedelta
from typing import List, Optional
import threading
import time

from database import get_db, init_db, engine, Base
from models import AggregatedSensorData
from schemas import AggregatedSensorDataResponse, AggregatedSensorDataCreate
from kafka_consumer import consume_kafka_messages

# FastAPI 앱 생성
app = FastAPI(title="Logistics Sensor Backend", version="1.0.0")

# CORS 설정 (프론트엔드와 통신)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 앱 시작 시 DB 초기화
@app.on_event("startup")
async def startup_event():
    """앱 시작 시 DB 초기화 및 Kafka 컨슈머 시작"""
    print("[시작] 데이터베이스 초기화 중...")
    
    # 모델 import를 먼저 해서 Base에 등록되게 함
    from models import AggregatedSensorData
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("[완료] 데이터베이스 테이블 생성 완료")
    
    # Kafka 컨슈머 시작
    print("[시작] Kafka 컨슈머 시작...")
    start_kafka_consumer()
    print("[완료] Kafka 컨슈머 시작됨")

# Kafka 컨슈머를 백그라운드 스레드로 실행
def start_kafka_consumer():
    kafka_thread = threading.Thread(target=consume_kafka_messages, daemon=True)
    kafka_thread.start()

# ===== API 엔드포인트 =====

@app.get("/api/health")
def health_check():
    """헬스 체크"""
    from database import engine
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM aggregated_sensor_data"))
            count = result.scalar()
        return {"status": "ok", "database": "connected", "records": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/sensors/latest", response_model=List[AggregatedSensorDataResponse])
def get_latest_sensor_data(
    zone_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    최신 센서 데이터 조회 (간단 버전)
    """
    try:
        query = db.query(AggregatedSensorData)
        
        if zone_id:
            query = query.filter(AggregatedSensorData.zone_id == zone_id)
        
        # 최신 데이터부터 정렬
        results = query.order_by(desc(AggregatedSensorData.id)).limit(limit).all()
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/sensors/history", response_model=List[AggregatedSensorDataResponse])
def get_sensor_history(
    zone_id: Optional[str] = None,
    aggregated_id: Optional[str] = None,
    hours: int = 24,
    limit: int = 500,
    db: Session = Depends(get_db)
):
    """
    센서 데이터 히스토리 조회 (시간 범위 기반)
    """
    query = db.query(AggregatedSensorData)
    
    # 시간 필터
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    query = query.filter(AggregatedSensorData.created_at >= time_threshold)
    
    if zone_id:
        query = query.filter(AggregatedSensorData.zone_id == zone_id)
    
    if aggregated_id:
        query = query.filter(AggregatedSensorData.aggregated_id == aggregated_id)
    
    results = query.order_by(desc(AggregatedSensorData.timestamp)).limit(limit).all()
    
    return results

@app.get("/api/zones/summary")
def get_zones_summary(
    hours: int = 1,
    db: Session = Depends(get_db)
):
    """
    각 Zone별 요약 정보 조회
    """
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    zones = db.query(AggregatedSensorData.zone_id).distinct().all()
    
    summary = []
    for (zone_id,) in zones:
        zone_data = db.query(AggregatedSensorData).filter(
            (AggregatedSensorData.zone_id == zone_id) &
            (AggregatedSensorData.created_at >= time_threshold)
        ).all()
        
        if not zone_data:
            continue
        
        total_throughput = sum(d.item_throughput for d in zone_data)
        avg_speed = sum(d.avg_speed for d in zone_data) / len(zone_data) if zone_data else 0
        bottleneck_count = sum(1 for d in zone_data if d.bottleneck_indicator.get('is_congested', False))
        
        summary.append({
            "zone_id": zone_id,
            "total_throughput": total_throughput,
            "avg_speed": round(avg_speed, 2),
            "bottleneck_count": bottleneck_count,
            "data_points": len(zone_data)
        })
    
    return summary

@app.get("/api/bottlenecks")
def get_bottlenecks(
    hours: int = 1,
    db: Session = Depends(get_db)
):
    """
    병목 현상 감지된 센서 조회
    """
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    congested = db.query(AggregatedSensorData).filter(
        (AggregatedSensorData.created_at >= time_threshold)
    ).all()
    
    bottlenecks = [
        {
            "aggregated_id": d.aggregated_id,
            "zone_id": d.zone_id,
            "bottleneck_score": d.bottleneck_indicator.get('bottleneck_score', 0),
            "timestamp": d.timestamp
        }
        for d in congested
        if d.bottleneck_indicator.get('is_congested', False)
    ]
    
    return sorted(bottlenecks, key=lambda x: x['bottleneck_score'], reverse=True)

@app.post("/api/sensors/data", response_model=AggregatedSensorDataResponse)
def create_sensor_data(
    data: AggregatedSensorDataCreate,
    db: Session = Depends(get_db)
):
    """
    센서 데이터 수동 저장 (테스트 용도)
    """
    sensor_record = AggregatedSensorData(
        aggregated_id=data.aggregated_id,
        zone_id=data.zone_id,
        line_direction=data.line_direction,
        timestamp=data.timestamp,
        aggregation_interval_sec=data.aggregation_interval_sec,
        item_throughput=data.item_throughput,
        avg_speed=data.avg_speed,
        sensor_status_breakdown=data.sensor_status_breakdown,
        bottleneck_indicator=data.bottleneck_indicator
    )
    db.add(sensor_record)
    db.commit()
    db.refresh(sensor_record)
    return sensor_record

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
