import threading
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List
from sensor_db import get_db, ZoneDataDB

"""
바스켓 이동 시뮬레이터

1초마다 각 바스켓의 위치를 계산하고 업데이트합니다.
- 바스켓이 라인을 따라 이동
- 라인 끝에 도달하면 상태를 "arrived"로 변경
- 동시성 관리를 위해 lock 사용

[이동 경로 결정 로직]
1. Zone 순차 이동 (Flow-based Routing):
   - Zone ID의 숫자 접두어(01-, 02-) 또는 물류 키워드(IB, SR, OB)를 기준으로 순서를 결정합니다.
   - 우선순위: 숫자 > 키워드(IB->SR->OB) > 알파벳순
   - 따라서 "IB-01" 같은 기존 이름도 자동으로 입고->보관->출고 순서로 인식됩니다.

2. Line 랜덤 분산 (Load Balancing):
   - 다음 Zone으로 이동할 때, 해당 Zone에 여러 라인이 있다면 그중 하나를 무작위로 선택합니다.
"""


class BasketMovement:
    """바스켓 이동 관리 클래스"""
    
    # 기본 통과 시간 (초)
    DEFAULT_TRANSIT_TIME = 50.0
    SAFE_DISTANCE_METERS = 1.0
    BOTTLENECK_GRACE_DISTANCE_METERS = 5.0  # 바스켓 투입 후 병목 체크 제외 거리
    ZONE_SPEED_CHOICES = [0.5, 1.0, 1.5]
    ZONE_SPEED_REFRESH_SEC = 10
    
    def __init__(self, basket_pool, zones):
        """
        Args:
            basket_pool: BasketPool 인스턴스
            zones: ZONES 설정 리스트
                [
                    {
                        "zone_id": "IB-01",
                        "zone_name": "입고",
                        "lines": 4,
                        "length": 50,
                        "sensors": 40
                    },
                    ...
                ]
        """
        self.basket_pool = basket_pool
        # 존 순서 결정 (스마트 정렬: 숫자 > IB/SR/OB > 알파벳)
        self.zones = sorted(zones, key=self._get_zone_sort_key)
        self.is_running = False
        self.stop_event = threading.Event()  # 종료 이벤트 추가
        self.movement_thread = None
        self.speed_thread = None
        self.lock = threading.RLock()  # 재진입 가능한 락 사용 (데드락 방지)
        
        # 바스켓별 위치 추적 (basket_id → position_meters)
        self.basket_positions: Dict[str, float] = {}
        
        # 바스켓별 라인 정보 (basket_id → {zone_id, line_id, line_length})
        self.basket_lines: Dict[str, dict] = {}
        
        # 통과 시간 (초) - 나중에 프론트에서 변경 가능
        self.transit_time = self.DEFAULT_TRANSIT_TIME

        # 라인별 구간 속도 관리 (line_id → [{ start, end, multiplier }])
        self.line_speed_zones: Dict[str, List[dict]] = {}
        self._initialize_line_speed_zones()

    def _get_zone_sort_key(self, zone):
        """존 정렬을 위한 키 생성 (물류 흐름 반영)"""
        zid = zone["zone_id"].upper()
        
        # 1. 숫자로 시작하는 경우 (예: 01-IB) -> 가장 높은 우선순위
        if len(zid) > 0 and zid[0].isdigit():
            return (0, zid)
            
        # 2. 표준 물류 키워드 포함 여부 (IB -> SR -> OB)
        if "IB" in zid:  # Inbound (입고)
            return (1, zid)
        if "SR" in zid:  # Storage/Rack (보관)
            return (2, zid)
        if "OB" in zid:  # Outbound (출고)
            return (3, zid)
            
        # 3. 그 외는 알파벳순
        return (4, zid)
    
    def start(self):
        """바스켓 이동 시뮬레이션 시작"""
        if self.is_running:
            print("[바스켓 이동] 이미 실행 중입니다")
            return False
        
        self.stop_event.clear()  # 이벤트 초기화
        with self.lock:
            self.is_running = True
            self.movement_thread = threading.Thread(
                target=self._movement_worker,
                daemon=True,
                name="BasketMovementWorker"
            )
            self.movement_thread.start()

            # 존 속도 변경 워커
            self.speed_thread = threading.Thread(
                target=self._zone_speed_worker,
                daemon=True,
                name="ZoneSpeedWorker"
            )
            self.speed_thread.start()
        
        print("[바스켓 이동] ========== 바스켓 이동 시뮬레이터 시작 ==========")
        print(f"[바스켓 이동] 통과 시간: {self.transit_time}초")
        return True
    
    def stop(self):
        """바스켓 이동 시뮬레이션 중지"""
        self.stop_event.set()  # 대기 중인 스레드를 즉시 깨움
        
        with self.lock:
            if not self.is_running:
                return False
            
            self.is_running = False
        
        # 스레드가 안전하게 종료될 때까지 잠시 대기
        if self.movement_thread and self.movement_thread.is_alive():
            self.movement_thread.join(timeout=1.0)
        if self.speed_thread and self.speed_thread.is_alive():
            self.speed_thread.join(timeout=1.0)
            
        print("[바스켓 이동] 바스켓 이동 시뮬레이터 중지")
        return True
    
    def set_transit_time(self, transit_time: float):
        """
        바스켓 통과 시간 설정 (프론트엔드에서 호출)
        
        Args:
            transit_time: 라인 통과 시간 (초)
        """
        with self.lock:
            self.transit_time = transit_time
        print(f"[바스켓 이동] 통과 시간 변경: {transit_time}초")
    
    def _movement_worker(self):
        """메인 이동 루프 - 1초마다 실행"""
        try:
            while not self.stop_event.is_set():  # 이벤트 기반 루프 체크
                self._update_basket_positions()
                # 1초 대기하되, 종료 신호(set)가 오면 즉시 리턴
                if self.stop_event.wait(1.0):
                    break
        
        except Exception as e:
            print(f"[바스켓 이동] ❌ 오류: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_running = False
            print("[바스켓 이동] 이동 워커 종료")
    
    def _update_basket_positions(self):
        """모든 바스켓의 위치 업데이트"""
        try:
            active_baskets = [
                b for b in self.basket_pool.get_all_baskets().values()
                if b["status"] in ("in_transit", "stopped")
            ]

            if not active_baskets:
                return

            # 라인별로 그룹화 후 병목/재출발 제어
            line_groups = {}
            for basket in active_baskets:
                self._ensure_tracking(basket)
                info = self.basket_lines.get(basket["basket_id"], {})
                line_id = info.get("line_id") or basket.get("line_id")
                if not line_id:
                    continue
                if line_id not in line_groups:
                    line_groups[line_id] = []
                pos = self.basket_positions.get(basket["basket_id"], 0.0)
                line_groups[line_id].append((basket, pos, info))

            for line_id, items in line_groups.items():
                # 진행 순서: 선두 → 후행 (position 높은 순)
                items.sort(key=lambda x: x[1], reverse=True)
                released_in_group = False  # 병목 그룹당 1개씩만 재출발

                for idx, (basket, pos, info) in enumerate(items):
                    basket_id = basket["basket_id"]
                    line_id = info.get("line_id") or basket.get("line_id")
                    speed_modifier = self._get_speed_at_position(line_id, pos)
                    motion_state = basket.get("motion_state", "moving")
                    
                    # 선두 바스켓 처리
                    if idx == 0:
                        # 선두가 정지 상태면 즉시 재출발
                        if motion_state == "stopped":
                            self._resume_basket(basket_id)
                        # 선두는 항상 이동
                        self._move_basket(basket, speed_modifier)
                        continue
                    
                    # 후행 바스켓: 안전거리 확인
                    lead_pos = items[idx - 1][1]
                    gap = lead_pos - pos
                    
                    # 바스켓이 시작 구간 내인지 체크 (유예 거리)
                    is_grace_distance = pos < self.BOTTLENECK_GRACE_DISTANCE_METERS
                    
                    if gap < self.SAFE_DISTANCE_METERS and not is_grace_distance:
                        # 안전거리 부족 + 유예구간 아님 -> 정지
                        if motion_state != "stopped":
                            self._mark_bottleneck(basket_id)
                        # 정지 상태 유지 (이동하지 않음)
                        continue
                    
                    # 안전거리 확보됨 또는 유예구간
                    if motion_state == "stopped":
                        # 정지 중이었다면 순차 재출발 (라인당 1개씩)
                        if not released_in_group:
                            self._resume_basket(basket_id)
                            released_in_group = True
                            self._move_basket(basket, speed_modifier)
                        # 이미 재출발한 바스켓이 있으면 대기
                        continue
                    
                    # 정상 주행 중
                    self._move_basket(basket, speed_modifier)
        
        except Exception as e:
            print(f"[바스켓 이동] 위치 업데이트 오류: {e}")
    
    def _move_basket(self, basket: dict, speed_modifier: float = 1.0):
        """단일 바스켓의 위치 계산 및 이동"""
        basket_id = basket["basket_id"]
        zone_id = basket["zone_id"]
        line_id = basket["line_id"]
        
        self._ensure_tracking(basket)
        current_pos = self.basket_positions[basket_id]
        line_info = self.basket_lines[basket_id]
        line_length = line_info["line_length"]
        
        # 1초당 이동 거리 계산
        # 예: 50m을 50초에 통과 → 1m/초
        distance_per_second = (line_length / self.transit_time) * speed_modifier
        
        # 새로운 위치 계산
        new_pos = current_pos + distance_per_second
        
        # 로깅 (10%마다)
        progress = int((new_pos / line_length) * 100)
        prev_progress = int((current_pos / line_length) * 100)
        if progress != prev_progress and progress % 10 == 0:
            print(f"[바스켓 이동] {basket_id}: {progress}% 진행 ({new_pos:.2f}m / {line_length}m)")
        
        # 라인 끝 도달
        if new_pos >= line_length:
            self._complete_basket_transit(basket_id, basket)
        else:
            # 위치 업데이트
            with self.lock:
                self.basket_positions[basket_id] = new_pos
    
    def _ensure_tracking(self, basket: dict):
        """바스켓 위치/라인 기본값 보장"""
        basket_id = basket["basket_id"]
        if basket_id not in self.basket_positions:
            self.basket_positions[basket_id] = 0.0
        if basket_id not in self.basket_lines:
            self.basket_lines[basket_id] = {
                "zone_id": basket.get("zone_id"),
                "line_id": basket.get("line_id"),
                "line_length": self._get_line_length(basket.get("zone_id"), basket.get("line_id"))
            }

    def _mark_bottleneck(self, basket_id: str):
        """후행 바스켓을 정지 상태로 표시"""
        with self.lock:
            self.basket_pool.update_basket_status(
                basket_id,
                "stopped",
                motion_state="stopped",
                is_bottleneck=True
            )

    def _resume_basket(self, basket_id: str):
        """정지된 바스켓을 순차적으로 재출발"""
        with self.lock:
            self.basket_pool.update_basket_status(
                basket_id,
                "in_transit",
                motion_state="moving",
                is_bottleneck=False
            )

    def _complete_basket_transit(self, basket_id: str, basket: dict):
        """바스켓이 라인을 완전히 통과"""
        zone_id = basket["zone_id"]
        line_id = basket["line_id"]
        
        # 다음 이동할 존과 라인 계산
        next_zone_id, next_line_id = self._get_next_hop(zone_id)
        
        if next_zone_id:
            print(f"[바스켓 이동] 🔄 {basket_id} 환승: {zone_id} -> {next_zone_id} ({next_line_id})")
            
            # 바스켓 상태 업데이트 (위치 변경, 상태는 여전히 in_transit)
            with self.lock:
                self.basket_pool.update_basket_status(
                    basket_id,
                    "in_transit",
                    zone_id=next_zone_id,
                    line_id=next_line_id,
                    motion_state="moving",
                    is_bottleneck=False
                )
                
                # 위치 정보 리셋 (새로운 라인의 0m 지점부터 시작)
                self.basket_positions[basket_id] = 0.0
                
                # 라인 정보 갱신
                self.basket_lines[basket_id] = {
                    "zone_id": next_zone_id,
                    "line_id": next_line_id,
                    "line_length": self._get_line_length(next_zone_id, next_line_id)
                }
        else:
            print(f"[바스켓 이동] ✅ {basket_id} 최종 도착 완료 ({zone_id}/{line_id})")
            
            # 바스켓 상태 업데이트: in_transit → arrived
            with self.lock:
                self.basket_pool.update_basket_status(
                    basket_id,
                    "arrived",
                    zone_id=zone_id,
                    line_id=line_id,
                    motion_state="idle",
                    is_bottleneck=False
                )
                
                # 위치 정보 정리 (시뮬레이션 대상에서 제외)
                if basket_id in self.basket_positions:
                    del self.basket_positions[basket_id]
                if basket_id in self.basket_lines:
                    del self.basket_lines[basket_id]
    
    def _get_line_length(self, zone_id: str, line_id: str = "A") -> float:
        """라인의 정확한 길이를 데이터베이스에서 조회"""
        try:
            db = next(get_db())
            length = ZoneDataDB.get_line_length(db, zone_id, line_id)
            db.close()
            return length
        except Exception as e:
            print(f"[바스켓 이동] ⚠️ 라인 길이 조회 실패: {e}")
            return 50.0  # 기본값
            
    def _get_next_hop(self, current_zone_id: str):
        """현재 존의 다음 연결 존과 라인을 결정"""
        # 로직: zones 리스트 순서대로 이동 (Zone A -> Zone B -> Zone C)
        for i, zone in enumerate(self.zones):
            if zone["zone_id"] == current_zone_id:
                # 다음 존이 있는지 확인
                if i + 1 < len(self.zones):
                    next_zone = self.zones[i + 1]
                    
                    # 다음 존의 라인 중 하나를 랜덤 선택 (로드 밸런싱 효과)
                    # 라인 ID 형식: {ZONE_ID}-{001}
                    lines_val = next_zone.get("lines")
                    if isinstance(lines_val, list):
                        lines_count = len(lines_val)
                    else:
                        lines_count = int(lines_val) if lines_val else 1
                        
                    next_line_num = random.randint(1, lines_count)
                    next_line_id = f"{next_zone['zone_id']}-{next_line_num:03d}"
                    
                    return next_zone["zone_id"], next_line_id
        
        return None, None

    def _initialize_line_speed_zones(self):
        """모든 라인을 센서 기준으로 구간 분할하고 속도 계수 설정"""
        for zone in self.zones:
            zone_id = zone["zone_id"]
            line_count = zone.get("lines", 1)
            if isinstance(line_count, list):
                line_count = len(line_count)
            line_length = zone.get("length", 50.0)
            sensor_count = zone.get("sensors", 10)
            sensors_per_line = max(1, sensor_count // line_count) if line_count > 0 else 1
            
            # 각 라인별로 센서 개수만큼 구간 생성
            for line_num in range(1, line_count + 1):
                line_id = f"{zone_id}-{line_num:03d}"
                segment_length = line_length / sensors_per_line
                
                segments = []
                for i in range(sensors_per_line):
                    segments.append({
                        "start": i * segment_length,
                        "end": (i + 1) * segment_length,
                        "multiplier": 1.0
                    })
                self.line_speed_zones[line_id] = segments

    def _zone_speed_worker(self):
        """주기적으로 라인 구간별 속도 계수를 랜덤 변경"""
        while not self.stop_event.is_set():
            try:
                with self.lock:
                    # 전체 라인 중 일부를 선택
                    all_lines = list(self.line_speed_zones.keys())
                    if not all_lines:
                        continue
                    sample_size = max(1, int(len(all_lines) * 0.3))
                    selected_lines = random.sample(all_lines, sample_size)
                    
                    for line_id in selected_lines:
                        segments = self.line_speed_zones[line_id]
                        # 각 라인의 구간 중 일부를 랜덤 변경
                        num_segments_to_change = max(1, len(segments) // 3)
                        indices = random.sample(range(len(segments)), num_segments_to_change)
                        for idx in indices:
                            new_val = random.choice(self.ZONE_SPEED_CHOICES)
                            segments[idx]["multiplier"] = new_val
                        print(f"[구간 속도] {line_id}: {num_segments_to_change}개 구간 변경")
            except Exception as e:
                print(f"[구간 속도] 갱신 오류: {e}")
            finally:
                self.stop_event.wait(self.ZONE_SPEED_REFRESH_SEC)

    def _get_speed_at_position(self, line_id: str, position: float) -> float:
        """바스켓 위치에 해당하는 구간의 속도 계수 반환"""
        if not line_id or line_id not in self.line_speed_zones:
            return 1.0
        
        segments = self.line_speed_zones[line_id]
        for seg in segments:
            if seg["start"] <= position < seg["end"]:
                return seg["multiplier"]
        
        # 마지막 구간 (position >= end인 경우)
        if segments:
            return segments[-1]["multiplier"]
        return 1.0
    
    def get_basket_position(self, basket_id: str) -> dict:
        """바스켓의 현재 위치 조회"""
        with self.lock:
            if basket_id not in self.basket_positions:
                return None
            
            pos = self.basket_positions[basket_id]
            line_info = self.basket_lines.get(basket_id, {})
            
            return {
                "basket_id": basket_id,
                "position_meters": pos,
                "line_length": line_info.get("line_length", 0),
                "progress_percent": (pos / line_info.get("line_length", 1)) * 100 if line_info.get("line_length") else 0,
                "zone_id": line_info.get("zone_id"),
                "line_id": line_info.get("line_id"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    def get_all_positions(self) -> List[dict]:
        """모든 이동 중인 바스켓의 위치 조회"""
        with self.lock:
            positions = []
            for basket_id in self.basket_positions.keys():
                pos = self.get_basket_position(basket_id)
                if pos:
                    positions.append(pos)
            return positions
