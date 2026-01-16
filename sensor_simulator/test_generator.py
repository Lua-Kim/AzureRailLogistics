from sensor_data_generator import SensorDataGenerator

generator = SensorDataGenerator()

# 활성 센서 확인
total_active = sum(len(sensors) for sensors in generator.active_sensors.values())
print(f"활성 센서: {total_active}개\n")

# 활성 센서별 이벤트 샘플
active_sensors = generator.get_active_sensors()
print(f"첫 5개 활성 센서 이벤트:")
for i, (zone_id, sensor_info) in enumerate(active_sensors[:5]):
    event = generator.generate_single_event(zone_id, sensor_info)
    print(f"{i+1}. Zone: {event['zone_id']}, Sensor: {event['sensor_id']}, Signal: {event['signal']}, Direction: {event['direction']}")
