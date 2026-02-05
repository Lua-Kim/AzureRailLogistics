import json
import os
import asyncio
import threading
import time
import logging
from typing import List
from datetime import datetime
from azure.eventhub.aio import EventHubConsumerClient

# Configure logging for EventHub SDK
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eventhub_consumer")
logger.setLevel(logging.DEBUG)

# Set EventHub SDK logging  
# logging.getLogger("azure.eventhub").setLevel(logging.DEBUG)
# logging.getLogger("azure.eventhub._pyamqp").setLevel(logging.DEBUG)

class SensorEventConsumer:
    """IoT Hub Event Hub 호환 엔드포인트에서 센서 이벤트를 수신하는 Consumer"""
    
    def __init__(self, basket_pool=None, sensor_line_mapping=None):
        # IoT Hub Event Hub 호환 연결 문자열
        connection_str = os.getenv("EVENTHUB_CONNECTION_STRING")
        if not connection_str:
            raise ValueError("EVENTHUB_CONNECTION_STRING 환경 변수가 설정되지 않았습니다.")
        
        consumer_group = os.getenv("EVENTHUB_CONSUMER_GROUP") # 기본값은 $Default 없는 걸로 수정함. 26.02.05
        if not consumer_group or consumer_group.strip() == "":
            consumer_group = "$Default"
            print(f"[EventHubConsumer] WARNING: EVENTHUB_CONSUMER_GROUP not set, using fallback: $Default")
        
        self.connection_str = connection_str
        self.consumer_group = consumer_group
        self.client = None
        self.latest_events = []  # 최근 이벤트 저장 (메모리 캐시)
        self.max_events = 2000  # 최대 2000개까지 유지
        self.is_running = False
        self.loop = None
        self.thread = None
        
        # ====== 바스켓 위치 추적용 ======
        self.basket_pool = basket_pool
        self.sensor_line_mapping = sensor_line_mapping or {}  # {sensor_id: {line_id, position_m, line_length}}
        
        # ====== 배치 저장용 ======
        self.event_buffer = []      # 이벤트 버퍼
        self.buffer_size = 200      # 배치 크기 (200개로 증가)
        self.buffer_lock = threading.Lock()
        self.flush_thread = None    # 주기적 플러시 스레드
        self.buffer_flush_interval = 2  # 2초마다 플러시
        self.db_semaphore = threading.Semaphore(5)  # DB 접근 동시성 제한 (최대 5개 스레드)
        
    def start(self):
        """Start Consumer"""
        if self.is_running:
            print("[EventHubConsumer] Already running, skipping start")
            return
            
        self.is_running = True
        print(f"[EventHubConsumer] Starting with Consumer Group={self.consumer_group}")
        
        # Start batch flush thread
        self.flush_thread = threading.Thread(
            target=self._flush_buffer_periodically,
            daemon=True
        )
        self.flush_thread.start()
        print("[EventHubConsumer] Batch flush thread started")
        
        # Run in new event loop
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
        print("[EventHubConsumer] Async consumer thread started")
        
    def _run_async_loop(self):
        """비동기 이벤트 루프 실행"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._consume_loop())
        
    async def _consume_loop(self):
        """Message reception loop"""
        try:
            self.client = EventHubConsumerClient.from_connection_string(
                self.connection_str,
                consumer_group=self.consumer_group,
            )
            print("[EventHubConsumer] Attempting EventHub connection...")
            print(f"[EventHubConsumer] Connection String: {self.connection_str[:80]}...")
            print(f"[EventHubConsumer] Consumer Group: {self.consumer_group}")
            
            async with self.client:
                # Get event hub properties
                properties = await self.client.get_eventhub_properties()
                print(f"[EventHubConsumer] SUCCESS: Connected to EventHub")
                print(f"[EventHubConsumer] Eventhub: {properties['eventhub_name']}, Partitions: {len(properties['partition_ids'])}")
                
                # Standard receive from all partitions
                print(f"[EventHubConsumer] Listening for messages...")
                await self.client.receive(
                    on_event=self._on_event,
                    starting_position="-1",  # Receive from latest messages
                )

        except Exception as e:
            print(f"[EventHubConsumer] CRITICAL ERROR in receive loop: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    async def _on_event(self, partition_context, event):
        """Event reception callback - add to buffer and update basket location"""
        if not self.is_running:
            return
        
        try:
            # Parse event data
            event_data = json.loads(event.body_as_str())
            
            # Only log when signal=True (detected)
            zone_id = event_data.get('zone_id', 'N/A')
            signal = event_data.get('signal', False)
            speed = event_data.get('speed', 0)
       
            sensor_id = event_data.get('sensor_id', 'N/A')
            basket_id = event_data.get('basket_id', 'N/A')
            print(f"[EventHubConsumer] ✅ SIGNAL DETECTED: zone_id={zone_id}, sensor_id={sensor_id}, signal={signal}, basket_id={basket_id}, speed={speed}")
        
            # 바스켓 위치 업데이트 (센서 신호가 감지되었을 때)
            if self.basket_pool and event_data.get("signal"):
                self._update_basket_position(event_data)
            
            # 최근 이벤트 메모리 캐시에 추가 (프론트엔드 조회용)
            self.latest_events.append(event_data)
            if len(self.latest_events) > self.max_events:
                self.latest_events.pop(0)
            
            # 배치 버퍼에 추가
            with self.buffer_lock:
                self.event_buffer.append(event_data)
                
                # 버퍼가 가득 차면 즉시 플러시
                if len(self.event_buffer) >= self.buffer_size:
                    self._flush_buffer()
                    print(f"[EventHubConsumer] Buffer full, flushed {self.buffer_size} events") 
            
            # 체크포인트 업데이트
            await partition_context.update_checkpoint(event)
            
        except Exception as e:
            print(f"[EventHubConsumer] Event processing error: {type(e).__name__}: {e}")
    
    def _flush_buffer_periodically(self):
        """Periodically flush buffer"""
        print("[EventHubConsumer] Batch flush thread started")
        while self.is_running:
            time.sleep(self.buffer_flush_interval)
            with self.buffer_lock:
                if self.event_buffer:
                    self._flush_buffer()
    
    def _flush_buffer(self):
        """배치로 DB에 저장 (동기식 호출 - 별도 스레드에서)"""
        if not self.event_buffer:
            return
        
        # 백그라운드에서 비동기로 저장
        buffer_copy = self.event_buffer.copy()
        self.event_buffer.clear()
        
        thread = threading.Thread(
            target=self._save_batch_to_db_with_lock,
            args=(buffer_copy,),
            daemon=True
        )
        thread.start()
    
    def _save_batch_to_db_with_lock(self, events):
        """세마포어로 DB 접근을 제한하는 래퍼"""
        with self.db_semaphore:
            self._save_batch_to_db(events)
    
    def _save_batch_to_db(self, events):
        """Save sensor events to DB (runs in separate thread)"""
        try:
            from database import SessionLocal
            from models import SensorEvent
            from sqlalchemy.exc import InvalidRequestError, OperationalError
            import traceback
            
            # Azure PostgreSQL 세션 생성 (재시도 로직)
            max_retries = 3
            db = None
            for retry_count in range(max_retries):
                try:
                    db = SessionLocal()
                    break
                except (InvalidRequestError, OperationalError) as e:
                    if retry_count < max_retries - 1:
                        print(f"[_save_batch_to_db] DB 연결 재시도 {retry_count + 1}/{max_retries}: {e}")
                        traceback.print_exc()
                        time.sleep(0.5)
                    else:
                        print(f"[_save_batch_to_db] ❌ DB 연결 실패 (최대 재시도 횟수 초과): {e}")
                        traceback.print_exc()
                        return
            
            if db is None:
                print(f"[_save_batch_to_db] ❌ DB 세션을 생성할 수 없습니다")
                return
            
            try:
                sensor_events = []
                signal_true_count = 0
                
                for event_data in events:
                    # Parse timestamp and keep timezone info (KST will be stored as-is)
                    timestamp = datetime.fromisoformat(event_data["timestamp"])
                    
                    sensor_kwargs = {
                        "timestamp": timestamp,
                        "zone_id": event_data.get("zone_id", ""),
                        "basket_id": event_data.get("basket_id"),
                        "sensor_id": event_data.get("sensor_id", ""),
                        "signal": event_data.get("signal", False),
                        "speed": event_data.get("speed", 0.0),
                    }

                    # signal=True일 때만 로깅
                    if event_data.get("signal"):
                        signal_true_count += 1
                        print(f"[DB] Saving signal=True: zone_id={event_data.get('zone_id')}, sensor_id={event_data.get('sensor_id')}, basket_id={event_data.get('basket_id')}")

                    # 구버전 모델 호환 (컬럼 존재할 때만 추가)
                    if hasattr(SensorEvent, "position_x"):
                        sensor_kwargs["position_x"] = event_data.get("position_x")

                    sensor_event = SensorEvent(**sensor_kwargs)
                    sensor_events.append(sensor_event)
                
                db.add_all(sensor_events)
                db.commit()
                # signal=True만 저장된 경우 로깅
                if signal_true_count > 0:
                    print(f"[DB] ✅ Batch saved: {signal_true_count} signal=True events + {len(sensor_events) - signal_true_count} signal=False events (Total: {len(sensor_events)})")
                
            except Exception as e:
                db.rollback()
                print(f"❌ 배치 저장 실패: {e}")
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ DB 연결 오류: {e}")
    
    def _update_basket_position(self, event_data: dict):
        """센서 이벤트를 기반으로 바스켓 위치 업데이트"""
        try:
            sensor_id = event_data.get("sensor_id")
            line_id = event_data.get("line_id")
            zone_id = event_data.get("zone_id")
            
            if not sensor_id or not line_id:
                return
            
            # 해당 라인의 모든 바스켓 조회
            all_baskets = self.basket_pool.get_all_baskets()
            line_baskets = [
                (bid, b) for bid, b in all_baskets.items() 
                if b.get("line_id") == line_id and b.get("status") in ["moving", "in_transit"]
            ]
            
            if not line_baskets:
                return
            
            # 센서 위치 정보 조회 (sensor_line_mapping에서)
            sensor_info = self.sensor_line_mapping.get(sensor_id)
            if not sensor_info:
                # 센서 매핑이 없으면 센서 ID에서 위치 추정 (예: ZONE-A-001-S003 -> 3번째 센서)
                # 간단한 추정: 센서 번호 기반
                return
            
            sensor_position_m = sensor_info.get("position_m", 0)
            line_length = sensor_info.get("line_length", 100)
            
            # 센서 근처(±2m)에 있는 바스켓 찾기
            for basket_id, basket in line_baskets:
                current_pos = basket.get("position_m", 0)
                
                # 센서 근처에 있으면 위치 업데이트
                if abs(current_pos - sensor_position_m) < 5.0:  # 5m 이내
                    # 위치 업데이트
                    progress_percent = (sensor_position_m / line_length * 100) if line_length > 0 else 0
                    self.basket_pool.update_basket_position(
                        basket_id=basket_id,
                        position_m=sensor_position_m,
                        progress_percent=min(progress_percent, 100)
                    )
                    # print(f"[위치 업데이트] {basket_id}: {sensor_position_m:.1f}m ({progress_percent:.1f}%)")
                    
        except Exception as e:
            print(f"[위치 업데이트 오류] {e}")
    
    def get_recent_events(self, limit: int = 100) -> List[dict]:
        """최근 이벤트 가져오기"""
        return self.latest_events[-limit:]
    
    def get_event_count(self) -> int:
        """수신한 이벤트 총 개수"""
        return len(self.latest_events)
    
    def stop(self):
        """Consumer 중지"""
        self.is_running = False
        
        # 남은 버퍼 플러시
        with self.buffer_lock:
            if self.event_buffer:
                self._flush_buffer()
        
        # 플러시 스레드 종료 대기
        if self.flush_thread:
            self.flush_thread.join(timeout=5)
        
        print("Event Hub Consumer 중지")