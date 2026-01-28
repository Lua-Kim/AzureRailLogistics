"""센서 어댑터 추상 인터페이스"""

from abc import ABC, abstractmethod
from typing import Dict, List


class SensorAdapter(ABC):
    """센서 데이터 소스 추상화 인터페이스"""
    
    @abstractmethod
    def start(self) -> bool:
        """센서 데이터 수집 시작
        
        Returns:
            bool: 시작 성공 여부
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """센서 데이터 수집 중지
        
        Returns:
            bool: 중지 성공 여부
        """
        pass
    
    @abstractmethod
    def get_status(self) -> dict:
        """센서 시스템 상태 조회
        
        Returns:
            dict: {
                "running": bool,
                "source_type": str,
                "events_count": int,
                "additional_info": dict
            }
        """
        pass
    
    @abstractmethod
    def reset(self) -> bool:
        """센서 시스템 초기화 (시뮬레이터 전용)
        
        Returns:
            bool: 초기화 성공 여부
        """
        pass
