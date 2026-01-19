#!/usr/bin/env python3
"""빠른 테스트: 센서 시뮬레이터 import 확인"""

import sys
from pathlib import Path

# 경로 설정
backend_path = Path(__file__).parent / "backend"
sensor_sim_path = Path(__file__).parent / "sensor_simulator"

sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(sensor_sim_path))

print("=" * 60)
print("테스트: 센서 시뮬레이터 import 확인")
print("=" * 60)

try:
    print("\n1️⃣ sensor_simulator.sensor_db 로드...")
    from sensor_simulator.sensor_db import get_db, ZoneDataDB
    print("   ✅ 성공")
except Exception as e:
    print(f"   ❌ 실패: {e}")
    sys.exit(1)

try:
    print("\n2️⃣ sensor_simulator.basket_movement 로드...")
    from sensor_simulator.basket_movement import BasketMovement
    print("   ✅ 성공")
except Exception as e:
    print(f"   ❌ 실패: {e}")
    sys.exit(1)

try:
    print("\n3️⃣ sensor_simulator.sensor_data_generator 로드...")
    from sensor_simulator.sensor_data_generator import SensorDataGenerator
    print("   ✅ 성공")
except Exception as e:
    print(f"   ❌ 실패: {e}")
    sys.exit(1)

try:
    print("\n4️⃣ 데이터베이스 연결 테스트...")
    db = next(get_db())
    zones_config = ZoneDataDB.get_zones_config_for_sensor(db)
    print(f"   ✅ 성공 - {len(zones_config)}개 존 로드됨")
except Exception as e:
    print(f"   ❌ 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("모든 테스트 통과! 백엔드 실행 가능")
print("=" * 60)
