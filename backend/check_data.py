from database import SessionLocal
from models import AggregatedSensorData
import json

db = SessionLocal()
# 최근 데이터 조회
recent = db.query(AggregatedSensorData).order_by(AggregatedSensorData.created_at.desc()).limit(10).all()
print('최근 데이터 10개:')
for r in recent:
    bi = r.bottleneck_indicator if isinstance(r.bottleneck_indicator, dict) else json.loads(r.bottleneck_indicator or '{}')
    print(f'{r.aggregated_id}: speed={r.avg_speed:.2f}, score={bi.get("bottleneck_score", 0):.2f}, congested={bi.get("is_congested", False)}, time={r.created_at}')

# 병목으로 표시된 데이터 통계
congested_count = db.query(AggregatedSensorData).filter(
    AggregatedSensorData.bottleneck_indicator.contains('is_congested": true')
).count()
total_count = db.query(AggregatedSensorData).count()
print(f'\n총 데이터: {total_count}, 병목 데이터: {congested_count} ({congested_count/total_count*100:.1f}%)')
