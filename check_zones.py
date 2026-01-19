#!/usr/bin/env python3
"""데이터베이스의 존/라인 데이터 확인"""

import sys
from pathlib import Path

# 경로 설정
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from database import SessionLocal
from models import LogisticsZone, LogisticsLine

print("=" * 60)
print("데이터베이스 존/라인 데이터 확인")
print("=" * 60)

db = SessionLocal()

try:
    zones = db.query(LogisticsZone).all()
    print(f"\n존(Zone) 데이터: {len(zones)}개\n")
    
    if zones:
        for zone in zones:
            print(f"  {zone.zone_id} ({zone.name})")
            lines = db.query(LogisticsLine).filter(LogisticsLine.zone_id == zone.zone_id).all()
            print(f"    - 라인: {len(lines)}개")
            if lines:
                for line in lines[:2]:
                    print(f"      * {line.line_id}")
    else:
        print("  ❌ 존 데이터가 없습니다!")
        print("\n  → 데이터를 생성해야 합니다")
        
finally:
    db.close()

print("\n" + "=" * 60)
