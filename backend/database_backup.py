import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# .env 파일 로드
load_dotenv()

# PostgreSQL 연결 설정 (환경 변수에서만 읽음)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

engine = create_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def data_db():
    """데이터베이스 세션 반환"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_data_db():
    """데이터베이스 초기화 (테이블 생성만)"""
    Base.metadata.create_all(bind=engine)


# ============ Zone 헬퍼 함수 ============

class logis_data_db:
    """물류 데이터베이스 작업 클래스"""
    
    @staticmethod
    def save_zone_with_lines(db, zone_data):
        from models import LogisticsZone
        
        # 존 생성
        db_zone = LogisticsZone(**zone_data.dict())
        db.add(db_zone)
        db.flush()  # ID 생성
        
        # 라인 생성 (중앙화된 헬퍼 함수 사용)
        logis_data_db._create_lines_for_zone(
            db,
            zone_data.zone_id,
            zone_data.lines,
            zone_data.sensors,
            zone_data.length
        )
        
        db.refresh(db_zone)
        return db_zone
    
    @staticmethod
    def get_zone_by_id(db, zone_id):
        """존 조회 (라인 정보 포함)"""
        from models import LogisticsZone
        from sqlalchemy.orm import joinedload
        return db.query(LogisticsZone).options(joinedload(LogisticsZone.zone_lines)).filter(LogisticsZone.zone_id == zone_id).first()
    
    @staticmethod
    def get_all_zone_data(db):
        """모든 존 조회 (라인 정보 포함)"""
        from models import LogisticsZone
        from sqlalchemy.orm import joinedload
        return db.query(LogisticsZone).options(joinedload(LogisticsZone.zone_lines)).all()
    
    @staticmethod
    def update_zone_data(db, zone_id, zone_data):
        """존 업데이트"""
        db_zone = logis_data_db.get_zone_by_id(db, zone_id)
        if not db_zone:
            return None
        
        for key, value in zone_data.dict().items():
            setattr(db_zone, key, value)
        db.commit()
        db.refresh(db_zone)
        return db_zone
    
    @staticmethod
    def delete_zone_data(db, zone_id):
        """존 삭제 (라인도 함께 삭제됨)"""
        db_zone = logis_data_db.get_zone_by_id(db, zone_id)
        if not db_zone:
            return None
        
        db.delete(db_zone)
        db.commit()
        return zone_id
    
    @staticmethod
    def save_batch_zones(db, zones_list):
        """존 전체 설정 (기존 데이터 전부 교체)"""
        from models import LogisticsZone, LogisticsLine
        
        # 기존 데이터 삭제
        db.query(LogisticsZone).delete()
        db.query(LogisticsLine).delete()
        db.commit()
        
        # 새 데이터 추가 (라인 자동 생성)
        for zone_data in zones_list:
            logis_data_db.save_zone_with_lines(db, zone_data)
        
        return logis_data_db.get_all_zone_data(db)