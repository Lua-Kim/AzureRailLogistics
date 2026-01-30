# -*- coding: utf-8 -*-
"""
물류센터 프리셋 데이터 DB 초기화 스크립트 (SQLAlchemy 버전)

프론트엔드의 프리셋을 데이터베이스에 저장합니다.
실행: python init_presets_sqlalchemy.py
"""

import os
from sqlalchemy import create_engine, Column, String, Integer, Text, TIMESTAMP, ForeignKey, Index
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

Base = declarative_base()

# 데이터베이스 연결 문자열
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///logistics_presets.db')

# 모델 정의
class FacilityPreset(Base):
    __tablename__ = 'facility_presets'
    
    preset_key = Column(String(50), primary_key=True)
    preset_name = Column(String(100), nullable=False)
    description = Column(Text)
    total_zones = Column(Integer, nullable=False)
    total_lines = Column(Integer, nullable=False)
    total_length_m = Column(Integer, nullable=False)
    total_sensors = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())


class PresetZone(Base):
    __tablename__ = 'preset_zones'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    preset_key = Column(String(50), ForeignKey('facility_presets.preset_key', ondelete='CASCADE'), nullable=False)
    zone_id = Column(String(50), nullable=False)
    zone_name = Column(String(100), nullable=False)
    lines = Column(Integer, nullable=False)
    length_m = Column(Integer, nullable=False)
    sensors = Column(Integer, nullable=False)
    zone_order = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
    
    __table_args__ = (Index('idx_preset_zones_key', 'preset_key'),)


# 프리셋 데이터
PRESETS = {
    'mfc': {
        'name': '소형/도심 MFC',
        'description': '도심 내 위치, 라스트마일 배송 및 마이크로 풀필먼트',
        'zones': [
            {'zone_id': '01-PK', 'zone_name': '도심 피킹', 'lines': 20, 'length': 300, 'sensors': 300},
            {'zone_id': '02-SO', 'zone_name': '패킹/출고', 'lines': 20, 'length': 200, 'sensors': 200},
        ]
    },
    'tc': {
        'name': '통과형 센터 (TC)',
        'description': '보관 없이 분류 후 바로 배송하는 크로스도킹 중심',
        'zones': [
            {'zone_id': '01-XD', 'zone_name': '크로스도킹', 'lines': 40, 'length': 1500, 'sensors': 1500},
        ]
    },
    'dc': {
        'name': '광역 배송 센터 (DC)',
        'description': '대형 물류센터, 입고-보관-피킹-출고 전 프로세스',
        'zones': [
            {'zone_id': '01-IB', 'zone_name': '입고', 'lines': 40, 'length': 800, 'sensors': 800},
            {'zone_id': '02-ST', 'zone_name': '보관', 'lines': 100, 'length': 2000, 'sensors': 2000},
            {'zone_id': '03-PK', 'zone_name': '피킹', 'lines': 80, 'length': 1500, 'sensors': 1500},
            {'zone_id': '04-OB', 'zone_name': '출고', 'lines': 40, 'length': 800, 'sensors': 800},
        ]
    },
    'megaFc': {
        'name': '메가 풀필먼트 (FC)',
        'description': '이커머스 전용, 검수/가공/분류까지 포함한 대형 FC',
        'zones': [
            {'zone_id': '01-IB', 'zone_name': '입고', 'lines': 40, 'length': 800, 'sensors': 800},
            {'zone_id': '02-IS', 'zone_name': '검수', 'lines': 40, 'length': 600, 'sensors': 600},
            {'zone_id': '03-ST', 'zone_name': '랙 보관', 'lines': 200, 'length': 3000, 'sensors': 3000},
            {'zone_id': '04-PK', 'zone_name': '피킹', 'lines': 120, 'length': 2000, 'sensors': 2000},
            {'zone_id': '05-PC', 'zone_name': '가공', 'lines': 30, 'length': 1000, 'sensors': 1000},
            {'zone_id': '06-SR', 'zone_name': '분류', 'lines': 80, 'length': 1500, 'sensors': 1500},
            {'zone_id': '07-OB', 'zone_name': '출고', 'lines': 40, 'length': 1200, 'sensors': 1200},
        ]
    },
    'superFc': {
        'name': '초대형 풀필먼트 (Super FC)',
        'description': '최대 규모 FC, 반품 처리까지 포함한 초대형 시설',
        'zones': [
            {'zone_id': '01-IB', 'zone_name': '입고', 'lines': 60, 'length': 1000, 'sensors': 1000},
            {'zone_id': '02-IS', 'zone_name': '검수', 'lines': 60, 'length': 800, 'sensors': 800},
            {'zone_id': '03-ST', 'zone_name': '대형 랙 보관', 'lines': 400, 'length': 4000, 'sensors': 4000},
            {'zone_id': '04-PK', 'zone_name': '자동 피킹', 'lines': 200, 'length': 3000, 'sensors': 3000},
            {'zone_id': '05-PC', 'zone_name': '가공/재작업', 'lines': 50, 'length': 1500, 'sensors': 1500},
            {'zone_id': '06-SR', 'zone_name': '지능형 분류', 'lines': 150, 'length': 2000, 'sensors': 2000},
            {'zone_id': '07-OB', 'zone_name': '출고/배송', 'lines': 80, 'length': 2000, 'sensors': 2000},
            {'zone_id': '08-RET', 'zone_name': '반품 처리', 'lines': 40, 'length': 1000, 'sensors': 1000},
        ]
    },
    'intlHub': {
        'name': '국제 물류 허브',
        'description': '수출입 통관 및 국제 물류 처리 전문',
        'zones': [
            {'zone_id': '01-IB', 'zone_name': '국제 입고', 'lines': 100, 'length': 2000, 'sensors': 2000},
            {'zone_id': '02-CS', 'zone_name': '통관/검사', 'lines': 80, 'length': 1500, 'sensors': 1500},
            {'zone_id': '03-SR', 'zone_name': '국제 분류', 'lines': 200, 'length': 2500, 'sensors': 2500},
            {'zone_id': '04-EX', 'zone_name': '수출 처리', 'lines': 120, 'length': 2000, 'sensors': 2000},
            {'zone_id': '05-OB', 'zone_name': '국제 출고', 'lines': 80, 'length': 1500, 'sensors': 1500},
        ]
    },
    'autoFc': {
        'name': '자동화 물류센터',
        'description': '로봇 및 자동화 설비 중심 고효율 FC',
        'zones': [
            {'zone_id': '01-SR', 'zone_name': '자동 분류', 'lines': 300, 'length': 3000, 'sensors': 3000},
            {'zone_id': '02-PK', 'zone_name': '로봇 피킹', 'lines': 250, 'length': 2500, 'sensors': 2500},
            {'zone_id': '03-RB', 'zone_name': '로봇 팔 처리', 'lines': 100, 'length': 2000, 'sensors': 2000},
            {'zone_id': '04-OB', 'zone_name': '자동 출고', 'lines': 150, 'length': 2000, 'sensors': 2000},
        ]
    }
}


def create_tables(engine):
    """테이블 생성"""
    print("📦 테이블 생성 중...")
    Base.metadata.create_all(engine)
    print("✅ 테이블 생성 완료\n")


def insert_presets(session):
    """프리셋 데이터 삽입"""
    print("📝 프리셋 데이터 삽입 중...")
    
    # 기존 데이터 삭제
    session.query(PresetZone).delete()
    session.query(FacilityPreset).delete()
    
    for preset_key, preset_data in PRESETS.items():
        zones = preset_data['zones']
        
        # 총합 계산
        total_zones = len(zones)
        total_lines = sum(z['lines'] for z in zones)
        total_length = sum(z['length'] for z in zones)
        total_sensors = sum(z['sensors'] for z in zones)
        
        # FacilityPreset 삽입
        facility_preset = FacilityPreset(
            preset_key=preset_key,
            preset_name=preset_data['name'],
            description=preset_data['description'],
            total_zones=total_zones,
            total_lines=total_lines,
            total_length_m=total_length,
            total_sensors=total_sensors
        )
        session.add(facility_preset)
        
        # PresetZone 삽입
        for idx, zone in enumerate(zones, start=1):
            preset_zone = PresetZone(
                preset_key=preset_key,
                zone_id=zone['zone_id'],
                zone_name=zone['zone_name'],
                lines=zone['lines'],
                length_m=zone['length'],
                sensors=zone['sensors'],
                zone_order=idx
            )
            session.add(preset_zone)
    
    session.commit()
    print("✅ 데이터 삽입 완료\n")


def verify_presets(session):
    """데이터 검증"""
    print("🔍 데이터 검증 중...\n")
    
    preset_count = session.query(FacilityPreset).count()
    zone_count = session.query(PresetZone).count()
    
    print(f"총 프리셋 개수: {preset_count}")
    print(f"총 존 개수: {zone_count}\n")
    
    print("=" * 80)
    print(f"{'Preset Key':<15} {'Name':<30} {'Zones':<8} {'Lines':<8} {'Sensors':<10}")
    print("=" * 80)
    
    presets = session.query(FacilityPreset).order_by(FacilityPreset.total_sensors.desc()).all()
    for preset in presets:
        print(f"{preset.preset_key:<15} {preset.preset_name:<30} {preset.total_zones:<8} {preset.total_lines:<8} {preset.total_sensors:<10}")
    
    print("=" * 80)
    
    # 최대 규모 프리셋 상세
    largest = session.query(FacilityPreset).order_by(FacilityPreset.total_sensors.desc()).first()
    if largest:
        print(f"\n📊 최대 규모 프리셋: {largest.preset_name} ({largest.preset_key})")
        print(f"   - Total Zones: {largest.total_zones}")
        print(f"   - Total Lines: {largest.total_lines}")
        print(f"   - Total Length: {largest.total_length_m}m")
        print(f"   - Total Sensors: {largest.total_sensors}")


def main():
    """메인 실행 함수"""
    print("📡 데이터베이스 연결 중...")
    
    # 저장할 DB 목록
    db_urls = []
    
    # 1. 환경변수에서 PostgreSQL URL 가져오기
    pg_url = os.getenv('DATABASE_URL')
    if pg_url:
        db_urls.append(('PostgreSQL', pg_url))
        print(f"✅ PostgreSQL 연결 준비")
    else:
        print(f"⚠️  DATABASE_URL 환경변수 없음 - PostgreSQL 스킵")
    
    # 2. 항상 SQLite에도 백업 저장
    sqlite_url = 'sqlite:///logistics_presets.db'
    db_urls.append(('SQLite', sqlite_url))
    print(f"✅ SQLite 연결 준비")
    
    if not db_urls:
        print("❌ 저장할 데이터베이스가 없습니다.")
        return
    
    print(f"\n총 {len(db_urls)}개 DB에 저장합니다.\n")
    
    # 각 DB에 저장
    for db_name, db_url in db_urls:
        print(f"\n{'='*80}")
        print(f"📂 {db_name} 처리 중...")
        print(f"{'='*80}\n")
        
        try:
            # 엔진 및 세션 생성
            engine = create_engine(db_url, echo=False)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # 1. 테이블 생성
            create_tables(engine)
            
            # 2. 데이터 삽입
            insert_presets(session)
            
            # 3. 검증
            verify_presets(session)
            
            session.close()
            print(f"\n✅ {db_name} 저장 완료!")
            
        except Exception as e:
            print(f"\n❌ {db_name} 오류 발생: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
    
    print(f"\n{'='*80}")
    print("✅ 모든 데이터베이스 처리 완료!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
