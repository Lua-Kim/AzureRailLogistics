#!/usr/bin/env python3
"""센서 신호 모니터링 - Kafka sensor-events 토픽 구독"""

from kafka import KafkaConsumer
import json
from datetime import datetime

print("=" * 70)
print("센서 신호 모니터링 시작")
print("=" * 70)
print("(Ctrl+C로 중지)\n")

consumer = KafkaConsumer(
    'sensor-events',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest',  # 최근 메시지부터 읽기
    consumer_timeout_ms=2000  # 2초 타임아웃
)

signal_true_count = 0
signal_false_count = 0
message_count = 0

try:
    for message in consumer:
        message_count += 1
        event = message.value
        
        zone = event.get("zone_id", "?")
        line = event.get("line_id", "?")
        sensor = event.get("sensor_id", "?")
        signal = event.get("signal", False)
        direction = event.get("direction", "?")
        
        if signal:
            signal_true_count += 1
            marker = "🟢"
        else:
            signal_false_count += 1
            marker = "🔴"
        
        # 5개마다 출력 (너무 많으니까)
        if message_count % 5 == 0:
            print(f"{marker} [{zone}/{line}] {sensor}: signal={signal} ({direction})")
            print(f"   📊 True: {signal_true_count}, False: {signal_false_count}")
        
        # 50개만 출력하고 중지
        if message_count >= 50:
            break

except KeyboardInterrupt:
    print("\n⏹️  모니터링 중지")

finally:
    consumer.close()

print("\n" + "=" * 70)
print(f"📈 결과: 총 {message_count}개 메시지")
print(f"   🟢 Signal TRUE:  {signal_true_count}개")
print(f"   🔴 Signal FALSE: {signal_false_count}개")
print("=" * 70)

if signal_true_count > 0:
    print("✅ 센서가 바스켓을 감지하고 있습니다!")
else:
    print("⚠️ 센서가 바스켓을 감지하지 않습니다")
