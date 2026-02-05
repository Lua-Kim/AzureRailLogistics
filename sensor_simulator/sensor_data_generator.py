import time
import json
import threading
import os
from datetime import datetime, timezone, timedelta
from azure.iot.device import IoTHubDeviceClient, Message
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AccessToken
import ssl
import urllib.parse

# 센�울 시간대 설정 (UTC+9)
KST = timezone(timedelta(hours=9))

# 센서_시뮬레이터의 database 모듈 import
try:
    from sensor_db import get_db, ZoneDataDB
except ImportError:
    # 백엔드에서 실행될 경우 경로 문제 해결을 위한 처리
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from sensor_db import get_db, ZoneDataDB

from basket_movement import BasketMovement

class SensorDataGenerator:
    """가상센서 데이터 생성 클래스"""
    
    def __init__(self, basket_pool=None, basket_movement=None):
        """
        Args:
            basket_pool: BasketPool 인스턴스 (선택사항)
            basket_movement: 외부에서 주입된 BasketMovement 인스턴스 (선택사항)
        """
        # Managed Identity를 사용한 IoT Hub 연결
        try:
            # 방법 1: 연결 문자열이 있으면 사용
            device_connection_string = os.getenv("IOT_HUB_DEVICE_CONNECTION_STRING")
            if device_connection_string:
                print("[Sensor Simulation] Connecting to IoT Hub using connection string...")
                self.iot_client = IoTHubDeviceClient.create_from_connection_string(device_connection_string)
            else:
                # Method 2: Using Managed Identity
                print("[Sensor Simulation] Connecting to IoT Hub using Managed Identity...")
                credential = DefaultAzureCredential()
                iothub_hostname = os.getenv("IOT_HUB_HOSTNAME", "LogisticsIoTHub.azure-devices.net")
                device_id = os.getenv("IOT_DEVICE_ID", "logistics-sensor-device")
                
                self.iot_client = IoTHubDeviceClient.create_from_azure_credential(
                    iothub_hostname=iothub_hostname,
                    device_id=device_id,
                    credential=credential
                )
            
            self.iot_client.connect()
            print("[Sensor Simulation] SUCCESS: IoT Hub connected")
            
        except Exception as e:
            print(f"[Sensor Simulation] FAILED: IoT Hub connection failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        self.is_running = False
        self.zones = {}
        self.stream_thread = None
        
        # DB에서 존 설정 로드
        self._load_zones_from_db()
        
        # 바스켓 풀 및 이동 시뮬레이터
        self.basket_pool = basket_pool
        self.basket_movement = basket_movement
        
        # If basket_pool exists but no movement, create internally (backward compatibility)
        if self.basket_pool and not self.basket_movement:
            self._initialize_basket_movement()
        elif self.basket_movement:
            print("[Sensor Simulation] External BasketMovement instance connected")
    
    def _setup_mqtt_direct_connection(self, device_connection_string):
        """MQTT Direct 연결 (SSL 검증 우회)"""
        import paho.mqtt.client as mqtt
        from azure.iot.device.common import connection_string_parser
        
        # 연결 문자열 파싱
        conn_dict = connection_string_parser.parse_connection_string(device_connection_string)
        hostname = conn_dict.get("HostName")
        device_id = conn_dict.get("DeviceId")
        shared_key = conn_dict.get("SharedAccessKey")
        
        # device_id 저장 (나중에 MQTT 토픽 구성에 사용)
        self.mqtt_device_id = device_id
        
        # MQTT 클라이언트 생성
        self.mqtt_client = mqtt.Client(client_id=device_id)
        
        # SSL 검증 비활성화
        self.mqtt_client.tls_set(
            ca_certs=None,
            certfile=None,
            keyfile=None,
            cert_reqs=ssl.CERT_NONE,
            tls_version=ssl.PROTOCOL_TLSv1_2,
            ciphers=None
        )
        self.mqtt_client.tls_insecure_set(True)  # SSL 검증 비활성화
        
        # 사용자명과 비밀번호 설정
        username = f"{hostname}/{device_id}/?api-version=2021-04-12"
        self.mqtt_client.username_pw_set(username, shared_key)
        
        # 콜백 등록
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
        
        # Connect
        print(f"[Sensor Simulation] Connecting to MQTT: {hostname}:8883")
        self.mqtt_client.connect(hostname, 8883, keepalive=60)
        self.mqtt_client.loop_start()
        
        # Wait for connection
        import time
        for _ in range(30):  # Max 30 second wait
            if hasattr(self, 'mqtt_connected') and self.mqtt_connected:
                return
            time.sleep(1)
        
        raise TimeoutError("MQTT connection timeout")
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            print("[Sensor Simulation] SUCCESS: MQTT connected")
            self.mqtt_connected = True
        else:
            print(f"[Sensor Simulation] FAILED: MQTT connection failed (code: {rc})")
            self.mqtt_connected = False
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        print(f"[Sensor Simulation] MQTT disconnected (code: {rc})")
        self.mqtt_connected = False
    
    def _load_zones_from_db(self):
        """데이터베이스에서 ZONES 설정 로드"""
        try:
            db = next(get_db())
            zones_config = ZoneDataDB.get_zones_config_for_sensor(db)
            
            self.zones = {}
            total_sensors = 0
            for zone in zones_config:
                self.zones[zone["zone_id"]] = zone
                total_sensors += zone["sensors"]
            
            print(f"[Sensor Simulation] Loaded {len(self.zones)} zones from DB")
            print(f"[Sensor Simulation] Total sensors: {total_sensors}")
            
        except Exception as e:
            print(f"[Sensor Simulation] FAILED: DB load failed: {e}")
            import traceback
            traceback.print_exc()
            # Don't proceed with empty configuration if DB connection fails
            self.zones = {}
    
    def _get_baskets_from_backend(self):
        """백엔드 API에서 현재 바스켓 상태 조회"""
        try:
            import requests
            # Docker 컨테이너 내부에서는 http://logistics-backend-dev:8000 사용
            # 로컬에서는 http://localhost:8000 사용
            backend_url = os.getenv("BACKEND_API_URL", "http://logistics-backend-dev:8000")
            response = requests.get(f"{backend_url}/baskets", timeout=2)
            if response.status_code == 200:
                data = response.json()
                baskets = data.get("baskets", [])
                # {line_id: [(basket_id, position_m), ...]}
                result = {}
                for basket in baskets:
                    if basket.get("status") in ["moving", "in_transit"]:
                        line_id = basket.get("line_id")
                        basket_id = basket.get("basket_id")
                        position_m = basket.get("position_m", 0)
                        if line_id:
                            if line_id not in result:
                                result[line_id] = []
                            result[line_id].append((basket_id, position_m))
                return result
        except Exception:
            pass
        return {}

    def _initialize_basket_movement(self):
        """Initialize basket movement simulator"""
        try:
            # Convert zones info to list and pass
            zones_list = list(self.zones.values())
            self.basket_movement = BasketMovement(self.basket_pool, zones_list)
            print("[Sensor Simulation] BasketMovement simulator initialized")
        except Exception as e:
            print(f"[Sensor Simulation] WARNING: BasketMovement init failed: {e}")

    def start(self):
        """Start sensor data generation"""
        print("[Sensor Simulation] Starting...")
        if self.is_running:
            print("[Sensor Simulation] Already running")
            return

        self.is_running = True
        print("[Sensor Simulation] is_running set to True")

        # basket_movement start (only control if internally created)
        if self.basket_movement and not self.basket_movement.is_running:
            # Check in case external instance already running
            try:
                self.basket_movement.start()
            except RuntimeError:
                pass # Already running, ignore

        self.stream_thread = threading.Thread(target=self._stream_sensor_data)
        self.stream_thread.daemon = True
        self.stream_thread.start()
        print("[Sensor Simulation] Data streaming thread started")

    def stop(self):
        """센서 데이터 생성 중지"""
        self.is_running = False
        if self.stream_thread:
            self.stream_thread.join()
            
        # basket_movement 중지 (내부 생성된 경우에만)
        if self.basket_movement and hasattr(self.basket_movement, 'stop'):
            self.basket_movement.stop()
        print("[Sensor Simulation] Stopping data stream...")
        self.is_running = False
        
        # Wait for thread to finish (with timeout)
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=5)
            print("[Sensor Simulation] Data streaming stopped")

    def _stream_sensor_data(self):
        """Periodically generate sensor data and send to IoT Hub"""
        import sys
        print("[Sensor Simulation] *** STREAM THREAD STARTED ***", flush=True)
        
        sys.stdout.flush()
        
        send_cycle = 0
        while self.is_running:
            start_time = time.time()
            send_cycle += 1
            
            try:
                events_sent = 0
                active_count = 0
                
                if not self.zones:
                    print("[Sensor Simulation] ERROR: No zones available!", flush=True)
                    sys.stdout.flush()
                
                for zone_id in self.zones:
                    events = self.generate_zone_events(zone_id)
                    # Filter to only signal=True events
                    events = [e for e in events if e.get("signal")]
                    # print(f"[Sensor Simulation] Zone {zone_id}: Generated {len(events)} signal events", flush=True)
                    # sys.stdout.flush()
                    
                    for event in events:
                        active_count += 1
                        try:
                            message_json = json.dumps(event)
                            
                            # Use IoTHubDeviceClient
                            if hasattr(self, 'iot_client') and self.iot_client:
                                message = Message(message_json)
                                message.content_type = "application/json"
                                message.content_encoding = "utf-8"
                                self.iot_client.send_message(message)
                                print(f"[Sensor Simulation] ✅ SIGNAL DETECTED: zone={zone_id}, sensor={event.get('sensor_id')}, basket={event.get('basket_id')}, signal=True", flush=True)
                                sys.stdout.flush()
                                events_sent += 1
                            # MQTT Direct
                            elif hasattr(self, 'mqtt_client') and self.mqtt_client:
                                topic = f"devices/{self.mqtt_device_id}/messages/events/"
                                self.mqtt_client.publish(topic, message_json, qos=1)
                                print(f"[Sensor Simulation] ✅ SIGNAL DETECTED (MQTT): zone={zone_id}, sensor={event.get('sensor_id')}, basket={event.get('basket_id')}", flush=True)
                                sys.stdout.flush()
                                events_sent += 1
                            else:
                                print("[Sensor Simulation] ⚠️ WARNING: No valid client available for signal=True event!", flush=True)
                                sys.stdout.flush()
                        except Exception as send_error:
                            print(f"[Sensor Simulation] ❌ ERROR: Message send failed (zone={zone_id}): {type(send_error).__name__}: {send_error}", flush=True)
                            sys.stdout.flush()
                
                # Print log only every 10 cycles
                if send_cycle % 10 == 0:
                    print(f"[Sensor Simulation] Cycle #{send_cycle}: Active signals detected: {active_count}", flush=True)
                    sys.stdout.flush()
                
            except Exception as e:
                print(f"[Sensor Simulation] ❌ CRITICAL ERROR: {type(e).__name__}: {e}", flush=True)
                import traceback
                traceback.print_exc()
                sys.stdout.flush()
            
            # Wait to maintain 1 second interval
            elapsed = time.time() - start_time
            sleep_time = max(0, 1.0 - elapsed)
            time.sleep(sleep_time)

    def generate_sensor_id(self, zone_id: str, sensor_number: int) -> str:
        """센서 ID 생성"""
        zone_prefix = zone_id.replace("-", "")
        return f"SENSOR-{zone_prefix}{sensor_number:05d}"

    def generate_zone_events(self, zone_id: str, event_count: int = None) -> list:
        """특정 구역의 모든 센서 이벤트 생성 (바스켓 위치 연동)"""
        events = []
        zone_data = self.zones.get(zone_id)
        if not zone_data:
            return []
            
        # UTC 시간으로 timestamp 생성 (DB에 UTC로 저장)
        timestamp = datetime.now(timezone.utc).isoformat()
        lines = zone_data.get("lines", [])
        
        # [Fix] lines가 int인 경우 list로 변환 (구버전 DB 호환 및 방어 코드)
        if isinstance(lines, int):
            line_count = lines
            lines = []
            default_length = zone_data.get("length", 50.0)
            for i in range(line_count):
                lines.append({
                    "line_id": f"{zone_id}-{i+1:03d}",
                    "length": default_length
                })
        
        # [성능 최적화] 해당 구역의 바스켓 위치를 미리 조회하여 라인별로 그룹화
        # 매 센서마다 전체 바스켓을 조회하는 비효율(O(N*M))을 제거 -> O(N+M)으로 개선
        baskets_in_zone = {} # {line_id: [(basket_id, pos_meters), ...]}
        
        # 먼저 basket_movement에서 시도
        if self.basket_movement:
            with self.basket_movement.lock:
                for basket_id, info in self.basket_movement.basket_lines.items():
                    if str(info.get("zone_id")).strip() == str(zone_id).strip():
                        lid = info.get("line_id")
                        pos = self.basket_movement.basket_positions.get(basket_id)
                        if lid and pos is not None:
                            if lid not in baskets_in_zone:
                                baskets_in_zone[lid] = []
                            baskets_in_zone[lid].append((basket_id, pos))
        
        # Also fetch backend baskets to support both local simulation and backend-deployed baskets
        backend_baskets = self._get_baskets_from_backend()
        if backend_baskets:
            # 해당 zone의 라인만 필터링
            for line_id, basket_list in backend_baskets.items():
                # line_id가 zone_id로 시작하는지 확인
                if str(line_id).startswith(str(zone_id)):
                    if line_id not in baskets_in_zone:
                        baskets_in_zone[line_id] = []
                    # Add backend baskets to the list
                    baskets_in_zone[line_id].extend(basket_list)

        # 구역 내 모든 라인의 센서 상태 확인
        for line in lines:
            line_id = line["line_id"]
            length = float(line["length"])
            # 라인별 센서 개수 계산
            total_zone_sensors = zone_data.get("sensors", 0)
            total_zone_lines = len(lines)
            sensors_per_line = max(1, int(total_zone_sensors / total_zone_lines)) if total_zone_lines > 0 else 0
            
            interval = length / sensors_per_line if sensors_per_line > 0 else 1.0
            
            # 해당 라인에 있는 바스켓들의 위치 목록
            line_basket_positions = baskets_in_zone.get(line_id, [])
            
            DETECTION_RANGE = 0.5

            for i in range(sensors_per_line):
                sensor_pos = (i + 1) * interval
                
                # [최적화] 미리 분류된 바스켓 위치 목록에서만 검색 (훨씬 빠름)
                signal = False
                detected_position = None
                detected_basket_id = None
                for basket_id, b_pos in line_basket_positions:
                    if abs(b_pos - sensor_pos) <= DETECTION_RANGE:
                        signal = True
                        detected_position = b_pos
                        detected_basket_id = basket_id
                        break
                
                # 센서 위치에서의 속도 계수 조회
                speed_modifier = 1.0
                if self.basket_movement and detected_position is not None:
                    try:
                        speed_modifier = self.basket_movement._get_speed_at_position(line_id, detected_position)
                    except Exception:
                        speed_modifier = 1.0
                
                sensor_id = f"{line_id}-S{i+1:03d}"
                
                event = {
                    "zone_id": zone_id,
                    "line_id": line_id,
                    "sensor_id": sensor_id,
                    "basket_id": detected_basket_id,
                    "signal": signal,
                    "timestamp": timestamp,
                    "speed": 50.0 * speed_modifier if signal else 0.0,
                    "position_x": sensor_pos
                }
                events.append(event)
                
        return events

if __name__ == "__main__":
    # 단독 실행 테스트를 위한 메인 블록
    try:
        from basket_manager import BasketPool
    except ImportError:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from basket_manager import BasketPool

    print("="*60)
    print("[센서 시뮬레이터] 독립 실행 모드 시작")
    print("="*60)

    # 1. 바스켓 풀 생성
    basket_pool = BasketPool(pool_size=100)

    # 2. 센서 생성기 초기화 (BasketMovement는 내부에서 자동 생성됨)
    generator = SensorDataGenerator(basket_pool=basket_pool)

    # [테스트] 바스켓 5개 투입 (움직임 확인용)
    if generator.zones:
        # 첫 번째 존과 라인 찾기
        first_zone_id = list(generator.zones.keys())[0]
        lines = generator.zones[first_zone_id].get("lines", [])
        
        if lines and isinstance(lines, list) and len(lines) > 0:
            # lines가 딕셔너리 리스트인 경우
            first_line_id = lines[0].get("line_id") if isinstance(lines[0], dict) else f"{first_zone_id}-001"
            
            print(f"[Main] 테스트 바스켓 5개 투입 -> {first_zone_id} / {first_line_id}")
            for i in range(5):
                basket_pool.assign_basket(f"BASKET-{i+1:05d}", first_zone_id, first_line_id)

    # 3. 시작
    try:
        generator.start()
        print("[Main] 시뮬레이션 실행 중 (Ctrl+C로 종료)...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Main] 종료 요청 확인")
        generator.stop()
