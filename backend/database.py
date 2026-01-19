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
