"""센서 어댑터 팩토리 - 설정 기반 어댑터 생성"""

import os
from .base import SensorAdapter
from .simulator_adapter import SimulatorAdapter
from .real_sensor_adapter import RealSensorAdapter


def create_adapter(
    adapter_type: str = None,
    basket_pool=None,
    zones_config=None,
    sensor_config=None
) -> SensorAdapter:
    """센서 어댑터 생성 팩토리
    
    Args:
        adapter_type: "simulator" 또는 "real_sensor" (None이면 환경 변수에서 읽음)
        basket_pool: BasketPool 인스턴스 (시뮬레이터용)
        zones_config: 존 설정 (시뮬레이터용)
        sensor_config: 센서 설정 (실제 센서용)
    
    Returns:
        SensorAdapter: 생성된 어댑터 인스턴스
    
    Examples:
        # 시뮬레이터 사용
        adapter = create_adapter("simulator", basket_pool, zones_config)
        
        # 실제 센서 사용
        adapter = create_adapter("real_sensor", sensor_config={
            "gateway_url": "http://sensor.company.com",
            "kafka_broker": "localhost:9092"
        })
        
        # 환경 변수 기반
        # export SENSOR_ADAPTER=simulator
        adapter = create_adapter()
    """
    # 환경 변수에서 읽기 (기본값: simulator)
    if adapter_type is None:
        adapter_type = os.getenv("SENSOR_ADAPTER", "simulator").lower()
    
    print(f"[AdapterFactory] 센서 어댑터 생성: {adapter_type}")
    
    if adapter_type == "simulator":
        if basket_pool is None or zones_config is None:
            raise ValueError("시뮬레이터 어댑터는 basket_pool과 zones_config가 필요합니다")
        return SimulatorAdapter(basket_pool, zones_config)
    
    elif adapter_type == "real_sensor":
        if sensor_config is None:
            # 기본 설정
            sensor_config = {
                "gateway_url": os.getenv("SENSOR_GATEWAY_URL", "http://localhost:8080"),
                "protocol": os.getenv("SENSOR_PROTOCOL", "REST"),
                "kafka_broker": os.getenv("KAFKA_BROKER", "localhost:9092"),
                "polling_interval": int(os.getenv("SENSOR_POLL_INTERVAL", "1"))
            }
        return RealSensorAdapter(sensor_config)
    
    else:
        raise ValueError(f"알 수 없는 어댑터 타입: {adapter_type}. 'simulator' 또는 'real_sensor'를 사용하세요.")
