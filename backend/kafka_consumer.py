import json
import asyncio
from kafka import KafkaConsumer
from sqlalchemy.orm import Session
from models import AggregatedSensorData
from database import SessionLocal
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "logistics-sensors"

def consume_kafka_messages():
    """
    Kafka에서 집계 데이터를 소비하여 PostgreSQL에 저장합니다.
    """
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='backend-consumer'
    )

    logger.info(f"Kafka consumer started. Topic: {KAFKA_TOPIC}")

    db = SessionLocal()
    try:
        for message in consumer:
            try:
                logger.info(f"[수신] 메시지 받음: {str(message.value)[:100]}...")
                data = message.value
                
                # 배열인 경우 (일반적인 경우)
                if isinstance(data, list):
                    for item in data:
                        # timestamp를 문자열로 저장 (ISO format)
                        ts = item['timestamp'] if isinstance(item['timestamp'], str) else item['timestamp'].isoformat()
                        
                        sensor_record = AggregatedSensorData(
                            aggregated_id=item['aggregated_id'],
                            zone_id=item['zone_id'],
                            line_direction=item['line_direction'],
                            timestamp=ts,
                            aggregation_interval_sec=item['aggregation_interval_sec'],
                            item_throughput=item['item_throughput'],
                            avg_speed=item['avg_speed'],
                            sensor_status_breakdown=item['sensor_status_breakdown'],
                            bottleneck_indicator=item['bottleneck_indicator']
                        )
                        db.add(sensor_record)
                # 단일 객체인 경우
                else:
                    ts = data['timestamp'] if isinstance(data['timestamp'], str) else data['timestamp'].isoformat()
                    
                    sensor_record = AggregatedSensorData(
                        aggregated_id=data['aggregated_id'],
                        zone_id=data['zone_id'],
                        line_direction=data['line_direction'],
                        timestamp=ts,
                        aggregation_interval_sec=data['aggregation_interval_sec'],
                        item_throughput=data['item_throughput'],
                        avg_speed=data['avg_speed'],
                        sensor_status_breakdown=data['sensor_status_breakdown'],
                        bottleneck_indicator=data['bottleneck_indicator']
                    )
                    db.add(sensor_record)
                
                db.commit()
                logger.info(f"✓ DB 저장 완료: {len(data) if isinstance(data, list) else 1}건")
                
            except json.JSONDecodeError as je:
                logger.error(f"JSON 파싱 실패: {je}")
            except Exception as e:
                logger.error(f"저장 중 에러: {e}", exc_info=True)
                db.rollback()
    
    finally:
        consumer.close()
        db.close()

if __name__ == "__main__":
    consume_kafka_messages()
