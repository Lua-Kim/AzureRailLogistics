from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# SQLite 데이터베이스 (파일 기반, 설치 불필요)
DATABASE_URL = "sqlite:///./logistics.db"

# SQLite 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite는 단일 스레드이므로 필요
    echo=False
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

def init_db():
    """데이터베이스 테이블 초기화 (앱 시작 시 호출)"""
    Base.metadata.create_all(bind=engine)
    print("✓ SQLite 데이터베이스 초기화 완료: logistics.db")
