#!/usr/bin/env python3
"""
Event Hub에서 수신된 메시지 확인 스크립트
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

CONNECTION_STRING = os.getenv("EVENTHUB_CONNECTION_STRING")
CONSUMER_GROUP = os.getenv("EVENTHUB_CONSUMER_GROUP", "$Default")

if not CONNECTION_STRING:
    print("❌ EVENTHUB_CONNECTION_STRING이 설정되지 않았습니다")
    exit(1)

print("=" * 70)
print("Event Hub 메시지 모니터링")
print("=" * 70)
print(f"Consumer Group: {CONSUMER_GROUP}")
print()

try:
    from azure.eventhub import EventHubConsumerClient
    
    client = EventHubConsumerClient.from_connection_string(
        CONNECTION_STRING,
        consumer_group=CONSUMER_GROUP,
    )
    
    print("✅ Event Hub 연결 성공")
    print("메시지 대기 중... (30초)")
    print("-" * 70)
    
    message_count = 0
    
    def on_event(partition_context, event):
        global message_count
        message_count += 1
        try:
            body = event.body_as_str() if hasattr(event, 'body_as_str') else str(event.get_body())
            print(f"[{message_count}] {body}")
        except Exception as e:
            print(f"[{message_count}] 파싱 오류: {e}")
    
    def on_error(partition_context, error):
        print(f"❌ 파티션 {partition_context.partition_id} 오류: {error}")
    
    with client:
        # 최신 메시지부터 수신 (starting_position 파라미터 제거)
        client.receive(
            on_event=on_event,
            on_error=on_error,
        )
        
        import time
        time.sleep(30)  # 30초 대기
    
    print("-" * 70)
    print(f"총 수신 메시지: {message_count}개")
    
    if message_count == 0:
        print("\n⚠️  Event Hub에서 메시지를 받지 못했습니다.")
        print("   - 센서 시뮬레이터가 메시지를 보내고 있는지 확인하세요")
        print("   - IoT Hub → Event Hub 라우팅 설정을 확인하세요")
    else:
        print(f"\n✅ {message_count}개의 메시지를 수신했습니다!")
        
except ImportError as e:
    print(f"❌ 모듈 임포트 실패: {e}")
    print("설치 명령:")
    print("  pip install azure-eventhub")
except Exception as e:
    print(f"❌ 오류: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
