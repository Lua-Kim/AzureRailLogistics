import os
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# .env 파일 로드 (프로젝트 루트에서)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# PostgreSQL 연결 설정 (환경 변수에서만 읽음)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

engine = create_engine(DATABASE_URL, echo=False, pool_size=5, max_overflow=10, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """데이터베이스 세션 반환"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ZoneDataDB:
    """존(Zone)과 라인(Line) 데이터 조회 (순수 SQL, 모델 독립적)"""
    
    @staticmethod
    def get_zones_config_for_sensor(db) -> list:
        """센서 제너레이터용 ZONES 설정 생성
        
        순수 SQL 쿼리로 logistics_zones와 logistics_lines 테이블에서 조회
        
        Returns:
            [
                {
                    "zone_id": "IB-01",
                    "zone_name": "입고",
                    "lines": 4,
                    "length": 50,
                    "sensors": 40
                },
                ...
            ]
        """
        from sqlalchemy import text
        
        zones_config = []
        
        # Step 1: 모든 존 정보 조회
        zones_result = db.execute(
            text("""
                SELECT zone_id, name, lines, length, sensors 
                FROM logistics_zones 
                ORDER BY zone_id
            """)
        )
        zones = zones_result.fetchall()
        
        # Step 2: 각 존별로 라인 정보 조회
        for zone_row in zones:
            zone_id, zone_name, line_count, zone_length, sensor_count = zone_row
            
            # 라인별 센서 개수 합계 (또는 존 테이블의 sensors 값 사용)
            lines_result = db.execute(
                text("""
                    SELECT COUNT(*) as line_count, COALESCE(SUM(sensors), 0) as total_sensors
                    FROM logistics_lines 
                    WHERE zone_id = :zone_id
                """),
                {"zone_id": zone_id}
            )
            lines_info = lines_result.fetchone()
            actual_line_count = lines_info[0] if lines_info else line_count
            total_sensors = lines_info[1] if lines_info else sensor_count
            
            zones_config.append({
                "zone_id": zone_id,
                "zone_name": zone_name,
                "lines": actual_line_count,
                "length": zone_length,
                "sensors": total_sensors
            })
        
        return zones_config    
    @staticmethod
    def get_line_length(db, zone_id: str, line_id: str) -> float:
        """특정 라인의 길이 조회
        
        Args:
            db: 데이터베이스 세션
            zone_id: 존 ID
            line_id: 라인 ID
            
        Returns:
            라인 길이 (미터)
        """
        from sqlalchemy import text
        
        result = db.execute(
            text("""
                SELECT length FROM logistics_lines 
                WHERE zone_id = :zone_id AND line_id = :line_id
            """),
            {"zone_id": zone_id, "line_id": line_id}
        )
        row = result.fetchone()
        
        if row:
            return float(row[0])
        
        # 기본값: 50m
        return 50.0