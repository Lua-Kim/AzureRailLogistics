import json

with open('deployment.template.json', 'r') as f:
    data = json.load(f)

# systemModules
data['modulesContent']['$edgeAgent']['properties.desired']['systemModules']['edgeAgent']['settings']['createOptions'] = '{}'
data['modulesContent']['$edgeAgent']['properties.desired']['systemModules']['edgeHub']['settings']['createOptions'] = json.dumps(data['modulesContent']['$edgeAgent']['properties.desired']['systemModules']['edgeHub']['settings']['createOptions'])

# modules
modules = data['modulesContent']['$edgeAgent']['properties.desired']['modules']
for mod_name in ['backend', 'sensorSimulator', 'kafka', 'zookeeper', 'postgres']:
    if mod_name in modules:
        modules[mod_name]['settings']['createOptions'] = json.dumps(modules[mod_name]['settings']['createOptions'])

with open('deployment.json', 'w') as f:
    json.dump(data, f, indent=2)

print('✅ deployment.json 변환 완료')
