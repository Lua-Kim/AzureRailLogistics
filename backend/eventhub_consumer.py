import json
import os
import asyncio
import threading
from typing import List
from azure.eventhub.aio import EventHubConsumerClient

class SensorEventConsumer:
    """IoT Hub Event Hub 호환 엔드포인트에서 센서 이벤트를 수신하는 Consumer"""
    
    def __init__(self):
        # IoT Hub Event Hub 호환 연결 문자열
        connection_str = os.getenv("EVENTHUB_CONNECTION_STRING")
        if not connection_str:
            raise ValueError("EVENTHUB_CONNECTION_STRING 환경 변수가 설정되지 않았습니다.")
        
        consumer_group = os.getenv("EVENTHUB_CONSUMER_GROUP", "$Default")
        
        self.connection_str = connection_str
        self.consumer_group = consumer_group
        self.client = None
        self.latest_events = []  # 최근 이벤트 저장 (메모리)
        self.max_events = 2000  # 최대 2000개까지 유지
        self.is_running = False
        self.loop = None
        self.thread = None
        
    def start(self):
        """Consumer 시작"""
        if self.is_running:
            return
            
        self.is_running = True
        print(f"Event Hub Consumer 시작: Consumer Group={self.consumer_group}")
        
        # 새 이벤트 루프에서 실행
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
        
    def _run_async_loop(self):
        """비동기 이벤트 루프 실행"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._consume_loop())
        
    async def _consume_loop(self):
        """메시지 수신 루프"""
        self.client = EventHubConsumerClient.from_connection_string(
            self.connection_str,
            consumer_group=self.consumer_group,
        )
        
        async with self.client:
            await self.client.receive(
                on_event=self._on_event,
                starting_position="-1",  # 최신 메시지부터
            )
    
    async def _on_event(self, partition_context, event):
        """이벤트 수신 콜백"""
        if not self.is_running:
            return
        
        try:
            # 이벤트 데이터 파싱
            event_data = json.loads(event.body_as_str())
            
            # 최근 이벤트 목록에 추가
            self.latest_events.append(event_data)
            
            # 최대 개수 유지
            if len(self.latest_events) > self.max_events:
                self.latest_events.pop(0)
            
            # 체크포인트 업데이트
            await partition_context.update_checkpoint(event)
            
        except Exception as e:
            print(f"[EventHubConsumer] 이벤트 처리 오류: {e}")
    
    def get_recent_events(self, limit: int = 100) -> List[dict]:
        """최근 이벤트 가져오기"""
        return self.latest_events[-limit:]
    
    def stop(self):
        """Consumer 중지"""
        self.is_running = False
        if self.client:
            # 클라이언트 종료는 이벤트 루프에서 처리됨
            pass
        print("Event Hub Consumer 중지")
