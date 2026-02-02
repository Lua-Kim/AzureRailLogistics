import json
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

with open('deployment.template.json', 'r') as f:
    template_str = f.read()

# 환경 변수 치환
replacements = {
    '${MODULES.backend}': 'containerogis.azurecr.io/logistics-backend:latest',
    '${MODULES.sensorSimulator}': 'containerogis.azurecr.io/logistics-sensor-simulator:latest',
    '$CONTAINER_REGISTRY_USERNAME': os.getenv('CONTAINER_REGISTRY_USERNAME', 'containerogis'),
    '$CONTAINER_REGISTRY_PASSWORD': os.getenv('CONTAINER_REGISTRY_PASSWORD', ''),
    '$CONTAINER_REGISTRY_ADDRESS': os.getenv('CONTAINER_REGISTRY_ADDRESS', 'containerogis.azurecr.io'),
    '$EVENTHUB_CONNECTION_STRING': os.getenv('EVENTHUB_CONNECTION_STRING', ''),
    '$IOT_HUB_DEVICE_CONNECTION_STRING': os.getenv('IOT_HUB_DEVICE_CONNECTION_STRING', ''),
    '$AZ_POSTGRE_DATABASE_URL': os.getenv('AZ_POSTGRE_DATABASE_URL', ''),
}

for key, value in replacements.items():
    template_str = template_str.replace(key, value)

# JSON 파싱
data = json.loads(template_str)

# systemModules - createOptions를 JSON 문자열로 변환
data['modulesContent']['$edgeAgent']['properties.desired']['systemModules']['edgeAgent']['settings']['createOptions'] = '{}'
data['modulesContent']['$edgeAgent']['properties.desired']['systemModules']['edgeHub']['settings']['createOptions'] = json.dumps(data['modulesContent']['$edgeAgent']['properties.desired']['systemModules']['edgeHub']['settings']['createOptions'])

# modules - createOptions를 JSON 문자열로 변환
modules = data['modulesContent']['$edgeAgent']['properties.desired']['modules']
for mod_name in ['backend', 'sensorSimulator', 'kafka', 'zookeeper', 'postgres']:
    if mod_name in modules:
        modules[mod_name]['settings']['createOptions'] = json.dumps(modules[mod_name]['settings']['createOptions'])

with open('deployment.json', 'w') as f:
    json.dump(data, f, indent=2)

print('✅ deployment.json 변환 완료')
