import os
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# .env 파일 로드 (프로젝트 루트에서)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Azure PostgreSQL 연결 (백엔드와 동일)
AZ_POSTGRE_DATABASE_URL = os.getenv("AZ_POSTGRE_DATABASE_URL")

if not AZ_POSTGRE_DATABASE_URL:
    raise ValueError("AZ_POSTGRE_DATABASE_URL 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

# 연결 풀 설정
engine = create_engine(
    AZ_POSTGRE_DATABASE_URL, 
    echo=False, 
    pool_size=5, 
    max_overflow=10,
    pool_recycle=3600,  # 1시간마다 연결 재생성
    pool_pre_ping=True,
    connect_args={"sslmode": "require", "connect_timeout": 10}
)
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
    def get_line_length(db, zone_id: str, line_id: str) -> float:
        """라인 길이 조회"""
        from sqlalchemy import text
        result = db.execute(
            text("SELECT length FROM logistics_lines WHERE zone_id = :zone_id AND line_id = :line_id"),
            {"zone_id": zone_id, "line_id": line_id}
        )
        row = result.fetchone()
        return row[0] if row else 50.0

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
            
            # 라인 정보 상세 조회 (리스트로 반환)
            lines_result = db.execute(
                text("""
                    SELECT line_id, length, sensors
                    FROM logistics_lines 
                    WHERE zone_id = :zone_id
                    ORDER BY line_id
                """),
                {"zone_id": zone_id}
            )
            lines_rows = lines_result.fetchall()
            
            lines_data = []
            total_sensors = 0
            for l_row in lines_rows:
                lines_data.append({"line_id": l_row[0], "length": l_row[1], "sensors": l_row[2]})
                total_sensors += l_row[2]
            
            zones_config.append({
                "zone_id": zone_id,
                "zone_name": zone_name,
                "lines": lines_data,  # int가 아닌 list 반환
                "length": zone_length,
                "sensors": total_sensors if total_sensors > 0 else sensor_count
            })
        
        return zones_config
