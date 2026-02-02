import os
import time
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

# .env 파일 로드 (프로젝트 루트에서)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# PostgreSQL 연결 설정 (Azure PostgreSQL만 사용)
AZ_POSTGRE_DATABASE_URL = os.getenv("AZ_POSTGRE_DATABASE_URL")

# Azure PostgreSQL 반드시 필요
if not AZ_POSTGRE_DATABASE_URL:
    raise ValueError("❌ AZ_POSTGRE_DATABASE_URL 환경 변수가 설정되지 않았습니다. deployment.json을 확인하세요.")

print("[DB] ✅ Azure PostgreSQL에만 연결합니다.")
print(f"[DB] Server: {AZ_POSTGRE_DATABASE_URL.split('@')[1].split('/')[0]}")

# Azure PostgreSQL은 SSL 필수
# 연결 풀 크기 최적화 (Azure PostgreSQL 제한: 기본 100개)
engine = create_engine(
    AZ_POSTGRE_DATABASE_URL, 
    echo=False, 
    pool_size=5,  # 활성 연결 수
    max_overflow=10,  # 추가 연결 가능 수
    pool_recycle=3600,  # 1시간마다 연결 재생성 (Azure 연결 타임아웃 대비)
    pool_pre_ping=True,  # 사용 전 연결 상태 확인
    connect_args={"sslmode": "require", "connect_timeout": 10}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def data_db():
    """데이터베이스 세션 반환"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_data_db(retries: int = 10, delay_seconds: int = 3):
    """데이터베이스 초기화 (테이블 생성만). DB 준비 대기 포함."""
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as e:
            if attempt == retries:
                raise
            print(f"[DB] 연결 실패 ({attempt}/{retries}). {delay_seconds}s 후 재시도...")
            time.sleep(delay_seconds)


# ============ 물류 데이터베이스 CRUD 클래스 ============

class logis_data_db:
    """물류 데이터베이스 CRUD 클래스 - 순수 데이터 영속성만 담당"""
    
    # ============ 존 (Zone) CRUD ============
    
    @staticmethod
    def save_zone(db, zone_data):
        """
        존 저장 (존 정보만, 라인은 별도로 저장)
        UPSERT 패턴: 존재하면 UPDATE, 없으면 INSERT
        
        Args:
            db: SQLAlchemy Session
            zone_data: LogisticsZoneCreate 스키마
        
        Returns:
            저장된 LogisticsZone 인스턴스
        """
        from models import LogisticsZone
        
        # 기존 zone 존재 여부 확인
        db_zone = db.query(LogisticsZone).filter(LogisticsZone.zone_id == zone_data.zone_id).first()
        
        if db_zone:
            # 기존 zone 업데이트
            for key, value in zone_data.dict().items():
                setattr(db_zone, key, value)
        else:
            # 새로운 zone 생성
            db_zone = LogisticsZone(**zone_data.dict())
            db.add(db_zone)
        
        db.commit()
        db.refresh(db_zone)
        return db_zone
    
    @staticmethod
    def get_zone_by_id(db, zone_id):
        """존 조회 (라인 정보 포함)"""
        from models import LogisticsZone
        from sqlalchemy.orm import joinedload
        return db.query(LogisticsZone).options(joinedload(LogisticsZone.zone_lines)).filter(LogisticsZone.zone_id == zone_id).first()
    
    @staticmethod
    def get_all_zones(db):
        """모든 존 조회 (라인 정보 포함)"""
        from models import LogisticsZone
        from sqlalchemy.orm import joinedload
        return db.query(LogisticsZone).options(joinedload(LogisticsZone.zone_lines)).all()
    
    @staticmethod
    def update_zone(db, zone_id, zone_data):
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
    def delete_zone(db, zone_id):
        """존 삭제 (라인도 함께 삭제됨)"""
        db_zone = logis_data_db.get_zone_by_id(db, zone_id)
        if not db_zone:
            return None
        
        db.delete(db_zone)
        db.commit()
        return zone_id
    
    @staticmethod
    def delete_all_zones(db):
        """모든 존 삭제 (프리셋 적용 시 사용)"""
        from models import LogisticsZone
        db.query(LogisticsZone).delete()
        db.commit()
    
    # ============ 라인 (Line) CRUD ============
    
    @staticmethod
    def _convert_line_to_model(line_data):
        """라인 데이터를 LogisticsLine 모델로 변환 (공통 로직)"""
        from models import LogisticsLine
        
        if hasattr(line_data, 'dict'):
            return LogisticsLine(**line_data.dict())
        else:
            return LogisticsLine(**line_data)
    
    @staticmethod
    def save_line(db, line_data):
        """
        라인 저장 (단일 라인)
        
        Args:
            db: SQLAlchemy Session
            line_data: 라인 데이터 (dict 또는 스키마)
        
        Returns:
            저장된 LogisticsLine 인스턴스
        """
        db_line = logis_data_db._convert_line_to_model(line_data)
        db.add(db_line)
        db.commit()
        db.refresh(db_line)
        return db_line
    
    @staticmethod
    def save_lines(db, lines_data):
        """
        여러 라인 저장 (배치)
        UPSERT 패턴: 존재하면 UPDATE, 없으면 INSERT
        
        Args:
            db: SQLAlchemy Session
            lines_data: 라인 데이터 리스트
        
        Returns:
            저장된 LogisticsLine 인스턴스 리스트
        """
        from models import LogisticsLine
        saved_lines = []
        
        for line_data in lines_data:
            # 기존 라인 존재 여부 확인 (zone_id + line_id로 구분)
            line_dict = line_data.dict() if hasattr(line_data, 'dict') else line_data
            db_line = db.query(LogisticsLine).filter(
                LogisticsLine.zone_id == line_dict['zone_id'],
                LogisticsLine.line_id == line_dict['line_id']
            ).first()
            
            if db_line:
                # 기존 라인 업데이트
                for key, value in line_dict.items():
                    if hasattr(db_line, key):
                        setattr(db_line, key, value)
            else:
                # 새로운 라인 생성
                db_line = logis_data_db._convert_line_to_model(line_data)
                db.add(db_line)
            
            saved_lines.append(db_line)
        
        db.commit()
        return saved_lines
    
    @staticmethod
    def get_lines_by_zone(db, zone_id):
        """특정 존의 모든 라인 조회"""
        from models import LogisticsLine
        return db.query(LogisticsLine).filter(LogisticsLine.zone_id == zone_id).all()
    
    @staticmethod
    def delete_lines_by_zone(db, zone_id):
        """특정 존의 모든 라인 삭제"""
        from models import LogisticsLine
        db.query(LogisticsLine).filter(LogisticsLine.zone_id == zone_id).delete()
        db.commit()
    
    @staticmethod
    def delete_all_lines(db):
        """모든 라인 삭제 (프리셋 적용 시 사용)"""
        from models import LogisticsLine
        db.query(LogisticsLine).delete()
        db.commit()    
    # ============ 프리셋 조회 (Azure PostgreSQL) ============
    
    @staticmethod
    def get_current_preset(db):
        """현재 적용된 프리셋 정보 조회 (현재 zones/lines로부터)"""
        from models import LogisticsZone
        from sqlalchemy.orm import joinedload
        
        zones = db.query(LogisticsZone).options(joinedload(LogisticsZone.zone_lines)).all()
        
        if not zones:
            return None
        
        preset_info = {
            "total_zones": len(zones),
            "total_lines": sum(len(z.zone_lines) if z.zone_lines else 0 for z in zones),
            "total_sensors": sum(z.sensors or 0 for z in zones),
            "total_length_m": sum(z.length or 0 for z in zones),
            "zones": [
                {
                    "id": z.zone_id,
                    "name": z.name,
                    "lines": z.lines or 0,
                    "length": z.length or 0,
                    "sensors": z.sensors or 0
                }
                for z in zones
            ]
        }
        
        return preset_info