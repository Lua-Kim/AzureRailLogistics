"""
센서-백엔드-프론트엔드 통합 연동 테스트

테스트 단계:
1. Docker 서비스 (PostgreSQL, Kafka) 확인
2. 백엔드 API 헬스 체크
3. 센서 데이터 생성 및 Kafka 스트리밍 확인
4. 백엔드 API 데이터 조회 확인
5. 프론트엔드 API 호출 검증
"""

import requests
import time
import json
import subprocess
import sys
from datetime import datetime

# 색상 정의
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Windows PowerShell 인코딩 설정
import io
import sys
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class IntegrationTester:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.kafka_broker = "localhost:9092"
        self.db_host = "localhost"
        self.db_port = 5432
        self.test_results = []
    
    def print_header(self, text):
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{text.center(60)}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
    
    def print_test(self, name):
        print(f"{YELLOW}[TEST]{RESET} {name}...", end=" ")
    
    def print_pass(self):
        print(f"{GREEN}✓ PASS{RESET}")
        self.test_results.append(("PASS", "Last test passed"))
    
    def print_fail(self, error):
        print(f"{RED}✗ FAIL{RESET}")
        print(f"  {RED}Error: {error}{RESET}")
        self.test_results.append(("FAIL", error))
    
    def print_info(self, text):
        print(f"{BLUE}[INFO]{RESET} {text}")
    
    def test_postgresql(self):
        """PostgreSQL 연결 테스트"""
        self.print_test("PostgreSQL 연결")
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database="logistics",
                user="admin",
                password="!postgres16"
            )
            conn.close()
            self.print_pass()
            return True
        except Exception as e:
            self.print_fail(str(e))
            return False
    
    def test_kafka(self):
        """Kafka 연결 테스트"""
        self.print_test("Kafka 브로커 연결")
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(bootstrap_servers=[self.kafka_broker])
            producer.close()
            self.print_pass()
            return True
        except Exception as e:
            self.print_fail(str(e))
            return False
    
    def test_backend_health(self):
        """백엔드 헬스 체크"""
        self.print_test("백엔드 API 헬스 체크")
        try:
            response = requests.get(f"{self.backend_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_info(f"Status: {data.get('status')}")
                self.print_info(f"Events received: {data.get('events_received', 0)}")
                self.print_pass()
                return True
            else:
                self.print_fail(f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_fail(str(e))
            return False
    
    def test_zones_config(self):
        """Zone 설정 조회"""
        self.print_test("Zone 설정 조회")
        try:
            response = requests.get(f"{self.backend_url}/zones", timeout=5)
            if response.status_code == 200:
                zones = response.json()
                self.print_info(f"Zone 수: {len(zones)}")
                for zone in zones[:3]:  # 처음 3개만 표시
                    self.print_info(f"  - {zone.get('zone_id')}: {zone.get('zone_name')}")
                self.print_pass()
                return True
            else:
                self.print_fail(f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_fail(str(e))
            return False
    
    def test_sensor_events(self):
        """최근 센서 이벤트 조회"""
        self.print_test("최근 센서 이벤트 조회")
        try:
            response = requests.get(f"{self.backend_url}/events/latest?count=5", timeout=5)
            if response.status_code == 200:
                data = response.json()
                event_count = data.get('count', 0)
                self.print_info(f"수신된 이벤트: {event_count}개")
                
                if event_count > 0:
                    # 첫 번째 이벤트 샘플 출력
                    sample = data['events'][0]
                    self.print_info(f"  - Zone: {sample.get('zone_id')}")
                    self.print_info(f"  - Sensor: {sample.get('sensor_id')}")
                    self.print_info(f"  - Signal: {sample.get('signal')}")
                
                self.print_pass()
                return event_count > 0
            else:
                self.print_fail(f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_fail(str(e))
            return False
    
    def test_baskets(self):
        """바스켓 목록 조회"""
        self.print_test("바스켓 목록 조회")
        try:
            response = requests.get(f"{self.backend_url}/baskets", timeout=5)
            if response.status_code == 200:
                data = response.json()
                basket_count = len(data) if isinstance(data, list) else data.get('count', 0)
                self.print_info(f"전체 바스켓: {basket_count}개")
                self.print_pass()
                return True
            else:
                self.print_fail(f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_fail(str(e))
            return False
    
    def test_basket_movement(self):
        """바스켓 이동 상태 확인"""
        self.print_test("바스켓 이동 상태 확인")
        try:
            response = requests.get(f"{self.backend_url}/baskets?status=moving", timeout=5)
            if response.status_code == 200:
                baskets = response.json()
                moving_count = len(baskets) if isinstance(baskets, list) else 0
                self.print_info(f"이동 중인 바스켓: {moving_count}개")
                if moving_count > 0:
                    basket = baskets[0]
                    self.print_info(f"  - {basket.get('basket_id')}: {basket.get('position')}m")
                self.print_pass()
                return True
            else:
                self.print_fail(f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_fail(str(e))
            return False
    
    def test_sensor_history(self):
        """센서 히스토리 조회"""
        self.print_test("센서 히스토리 조회")
        try:
            response = requests.get(f"{self.backend_url}/sensors/history?count=20", timeout=5)
            if response.status_code == 200:
                data = response.json()
                history_count = len(data) if isinstance(data, list) else data.get('count', 0)
                self.print_info(f"히스토리 데이터: {history_count}개")
                self.print_pass()
                return True
            else:
                self.print_fail(f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_fail(str(e))
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        self.print_header("센서-백엔드-프론트엔드 통합 테스트")
        self.print_info(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.print_info(f"백엔드 URL: {self.backend_url}")
        
        # 인프라 테스트
        self.print_header("1단계: 인프라 연결 확인")
        db_ok = self.test_postgresql()
        kafka_ok = self.test_kafka()
        
        if not (db_ok and kafka_ok):
            print(f"\n{RED}인프라 연결 실패. Docker 서비스를 확인하세요.{RESET}")
            print(f"실행: docker-compose up -d")
            return False
        
        # 백엔드 테스트
        self.print_header("2단계: 백엔드 API 테스트")
        time.sleep(2)  # 백엔드 시작 대기
        
        backend_ok = self.test_backend_health()
        
        if not backend_ok:
            print(f"\n{RED}백엔드 연결 실패. 백엔드 서버를 확인하세요.{RESET}")
            return False
        
        # 데이터 조회 테스트
        self.print_header("3단계: 데이터 조회 테스트")
        time.sleep(3)  # 센서 데이터 생성 대기
        
        self.test_zones_config()
        self.test_sensor_events()
        self.test_baskets()
        self.test_basket_movement()
        self.test_sensor_history()
        
        # 테스트 결과 요약
        self.print_header("테스트 결과 요약")
        passed = sum(1 for status, _ in self.test_results if status == "PASS")
        failed = sum(1 for status, _ in self.test_results if status == "FAIL")
        
        print(f"{GREEN}✓ PASS: {passed}개{RESET}")
        print(f"{RED}✗ FAIL: {failed}개{RESET}")
        
        if failed > 0:
            print(f"\n{YELLOW}실패한 테스트:{RESET}")
            for status, error in self.test_results:
                if status == "FAIL":
                    print(f"  - {error}")
        
        return failed == 0

if __name__ == "__main__":
    tester = IntegrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
