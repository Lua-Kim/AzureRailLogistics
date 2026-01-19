#!/usr/bin/env python3
"""바스켓 위치 모니터링 - BasketMovement에서 직접 확인"""

import sys
from pathlib import Path
import time

# 경로 설정
backend_path = Path(__file__).parent / "backend"
sensor_sim_path = Path(__file__).parent / "sensor_simulator"

sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(sensor_sim_path))

from database import SessionLocal
from models import LogisticsZone, LogisticsLine
from basket_manager import BasketPool
from basket_movement import BasketMovement

print("=" * 70)
print("바스켓 위치 모니터링")
print("=" * 70)

# DB에서 존 정보 조회
db = SessionLocal()
zones_list = db.query(LogisticsZone).all()
db.close()

# ZONES 포맷으로 변환
ZONES = []
for zone in zones_list:
    ZONES.append({
        "zone_id": zone.zone_id,
        "zone_name": zone.name,
        "lines": zone.lines,
        "length": zone.length,
        "sensors": zone.sensors
    })

# BasketPool 초기화
basket_pool = BasketPool(pool_size=200, zones_lines_config=[])

# 먼저 바스켓 1개 생성
print("\n1️⃣ 바스켓 풀 상태:")
available = basket_pool.get_available_baskets()
print(f"   사용 가능한 바스켓: {len(available)}개")

# 바스켓 할당 (BASKET-00001)
print("\n2️⃣ 바스켓 할당:")
basket = basket_pool.assign_basket("BASKET-00001", "DC-IB", "A", "DC-OB")
if basket:
    print(f"   ✅ {basket['basket_id']} 할당됨")
    print(f"      - 상태: {basket['status']}")
    print(f"      - 위치: {basket['zone_id']}/{basket['line_id']}")
else:
    print(f"   ❌ 바스켓 할당 실패")

# BasketMovement 초기화 및 시작
print("\n3️⃣ Movement 시뮬레이터 시작:")
movement = BasketMovement(basket_pool, ZONES)
movement.start()
print(f"   ✅ 시작됨 (통과 시간: {movement.transit_time}초)")

# 10초 동안 위치 모니터링
print("\n4️⃣ 바스켓 위치 변화 (10초):")
for i in range(10):
    time.sleep(1)
    pos_info = movement.get_basket_position("BASKET-00001")
    if pos_info:
        progress = pos_info.get("progress_percent", 0)
        position = pos_info.get("position_meters", 0)
        print(f"   [{i+1}초] 위치: {position:.2f}m / {progress:.1f}% 진행")
    else:
        print(f"   [{i+1}초] 바스켓을 찾을 수 없음")

# 중지
movement.stop()
print("\n✅ 모니터링 완료")
print("=" * 70)

# 최종 바스켓 상태 확인
final_basket = basket_pool.get_basket("BASKET-00001")
if final_basket:
    print(f"\n최종 바스켓 상태:")
    print(f"  - ID: {final_basket['basket_id']}")
    print(f"  - 상태: {final_basket['status']}")
    print(f"  - 위치: {final_basket['zone_id']}/{final_basket['line_id']}")
