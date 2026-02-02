import json
import os
import asyncio
import threading
import time
from typing import List
from datetime import datetime
from azure.eventhub.aio import EventHubConsumerClient

class SensorEventConsumer:
    """IoT Hub Event Hub 호환 엔드포인트에서 센서 이벤트를 수신하는 Consumer"""
    
    def __init__(self, basket_pool=None, sensor_line_mapping=None):
        # IoT Hub Event Hub 호환 연결 문자열
        connection_str = os.getenv("EVENTHUB_CONNECTION_STRING")
        if not connection_str:
            raise ValueError("EVENTHUB_CONNECTION_STRING 환경 변수가 설정되지 않았습니다.")
        
        consumer_group = os.getenv("EVENTHUB_CONSUMER_GROUP", "$Default")
        
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
        self.buffer_size = 10       # 배치 크기 (테스트용: 10개)
        self.buffer_lock = threading.Lock()
        self.flush_thread = None    # 주기적 플러시 스레드
        self.buffer_flush_interval = 1  # 1초마다 플러시 (테스트용)
        
    def start(self):
        """Consumer 시작"""
        if self.is_running:
            return
            
        self.is_running = True
        print(f"Event Hub Consumer 시작: Consumer Group={self.consumer_group}")
        
        # 배치 플러시 스레드 시작
        self.flush_thread = threading.Thread(
            target=self._flush_buffer_periodically,
            daemon=True
        )
        self.flush_thread.start()
        
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
        try:
            self.client = EventHubConsumerClient.from_connection_string(
                self.connection_str,
                consumer_group=self.consumer_group,
            )
            print("[EventHubConsumer] EventHub 연결 시도...")
            
            async with self.client:
                print("[EventHubConsumer] ✅ EventHub 연결 성공, 메시지 대기 중...")
                await self.client.receive(
                    on_event=self._on_event,
                    starting_position="-1",  # 최신 메시지부터
                )
        except Exception as e:
            print(f"[EventHubConsumer] ❌ 수신 루프 오류: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    async def _on_event(self, partition_context, event):
        """이벤트 수신 콜백 - 버퍼에 추가 및 바스켓 위치 업데이트"""
        if not self.is_running:
            return
        
        try:
            # 이벤트 데이터 파싱
            event_data = json.loads(event.body_as_str())
            
            # 디버그 로그
            zone_id = event_data.get('zone_id', 'N/A')
            signal = event_data.get('signal', False)
            speed = event_data.get('speed', 0)
            print(f"[EventHubConsumer] 이벤트 수신: zone_id={zone_id}, signal={signal}, speed={speed}")
            
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
            
            # 체크포인트 업데이트
            await partition_context.update_checkpoint(event)
            
        except Exception as e:
            print(f"[EventHubConsumer] 이벤트 처리 오류: {type(e).__name__}: {e}")
    
    def _flush_buffer_periodically(self):
        """주기적으로 버퍼 플러시 (3초마다)"""
        print("[EventHubConsumer] 배치 플러시 스레드 시작")
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
            target=self._save_batch_to_db,
            args=(buffer_copy,),
            daemon=True
        )
        thread.start()
    
    def _save_batch_to_db(self, events):
        """센서 이벤트를 DB에 저장 (별도 스레드에서 실행)"""
        print(f"\n[_save_batch_to_db] 함수 호출됨 - {len(events)}개 이벤트 저장 준비")
        
        try:
            from database import SessionLocal
            from models import SensorEvent
            
            # Azure PostgreSQL 세션 생성
            db = SessionLocal()
            
            try:
                sensor_events = []
                print(f"[_save_batch_to_db] 이벤트 변환 시작...")
                
                for i, event_data in enumerate(events):
                    print(f"  [{i+1}/{len(events)}] timestamp={event_data.get('timestamp')}, zone_id={event_data.get('zone_id')}, basket_id={event_data.get('basket_id')}, sensor_id={event_data.get('sensor_id')}, signal={event_data.get('signal')}, speed={event_data.get('speed')}")
                    
                    sensor_kwargs = {
                        "timestamp": datetime.fromisoformat(event_data["timestamp"]),
                        "zone_id": event_data.get("zone_id", ""),
                        "basket_id": event_data.get("basket_id"),
                        "sensor_id": event_data.get("sensor_id", ""),
                        "signal": event_data.get("signal", False),
                        "speed": event_data.get("speed", 0.0),
                    }

                    # 구버전 모델 호환 (컬럼 존재할 때만 추가)
                    if hasattr(SensorEvent, "position_x"):
                        sensor_kwargs["position_x"] = event_data.get("position_x")

                    sensor_event = SensorEvent(**sensor_kwargs)
                    sensor_events.append(sensor_event)
                
                print(f"[_save_batch_to_db] {len(sensor_events)}개 SensorEvent 객체 생성 완료")
                print(f"[_save_batch_to_db] {len(sensor_events)}개 SensorEvent 객체 생성 완료")
                
                print(f"[_save_batch_to_db] DB add_all 시작...")
                db.add_all(sensor_events)
                print(f"[_save_batch_to_db] DB add_all 완료, commit 시작...")
                db.commit()
                print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] {len(sensor_events)}개 이벤트 DB 저장 완료")

                # 저장 직후 실제 DB에 데이터가 있는지 테스트
                try:
                    from sqlalchemy import text
                    count = db.execute(text('SELECT COUNT(*) FROM sensor_events')).scalar()
                    print(f"[TEST] sensor_events 테이블 row 수: {count}")
                    last = db.execute(text('SELECT id, created_at FROM sensor_events ORDER BY id DESC LIMIT 1')).fetchone()
                    if last:
                        print(f"[TEST] 가장 최근 row: id={last[0]}, created_at={last[1]}")
                except Exception as test_e:
                    print(f"[TEST] sensor_events 직접 조회 실패: {test_e}")
                
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