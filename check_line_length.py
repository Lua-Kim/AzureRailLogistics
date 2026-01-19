#!/usr/bin/env python3
"""로직스 라인 길이 확인"""

import sys
sys.path.insert(0, '/mnt/c/Users/EL0100/Desktop/AzureRailLogistics/sensor_simulator')

from sensor_db import get_db, ZoneDataDB

db = next(get_db())

# DC-IB/A 라인의 길이 확인
from sqlalchemy import text

result = db.execute(
    text("""
        SELECT zone_id, line_id, length FROM logistics_lines 
        WHERE zone_id = 'DC-IB' AND line_id = 'A'
    """)
)

row = result.fetchone()
if row:
    print(f"✅ DC-IB/A 라인 길이: {row[2]}m")
else:
    print(f"❌ DC-IB/A 라인을 찾을 수 없습니다")

# 모든 DC-IB 라인 확인
result = db.execute(
    text("""
        SELECT zone_id, line_id, length FROM logistics_lines 
        WHERE zone_id = 'DC-IB'
        ORDER BY line_id
    """)
)

rows = result.fetchall()
print(f"\n🔍 DC-IB 모든 라인 ({len(rows)}개):")
for row in rows:
    print(f"   {row[0]}/{row[1]}: {row[2]}m")

# logistics_zones에서 DC-IB 정보
result = db.execute(
    text("""
        SELECT zone_id, name, length, lines FROM logistics_zones
        WHERE zone_id = 'DC-IB'
    """)
)

row = result.fetchone()
if row:
    print(f"\n📊 존 정보:")
    print(f"   zone_id: {row[0]}")
    print(f"   name: {row[1]}")
    print(f"   zone_length: {row[2]}m")
    print(f"   lines_count: {row[3]}")

db.close()
