import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('AZ_POSTGRE_DATABASE_SVR'),
    user=os.getenv('AZ_POSTGRE_DATABASE_USER'),
    password=os.getenv('AZ_POSTGRE_DATABASE_PASSWORD'),
    database=os.getenv('AZ_POSTGRE_DATABASE_NAME'),
    port=os.getenv('AZ_POSTGRE_DATABASE_PORT')
)

cursor = conn.cursor()

# 프리셋 정보 삽입
presets_data = [
    ('mfc', '중형 물류센터'),
    ('tc', '크로스도킹센터'),
    ('dc', '배포센터'),
    ('megaFc', '메가 풀필먼트센터'),
    ('superFc', '슈퍼 풀필먼트센터'),
    ('intlHub', '국제허브센터'),
    ('autoFc', '자동화센터')
]

for preset_key, preset_name in presets_data:
    cursor.execute(
        'INSERT INTO presets (preset_key, preset_name) VALUES (%s, %s) ON CONFLICT DO NOTHING',
        (preset_key, preset_name)
    )

# 프리셋 존 정보 삽입
preset_zones_data = [
    # mfc
    ('mfc', '01-PK', '도심 피킹', 20, 300, 300),
    ('mfc', '02-SO', '패킹/출고', 20, 200, 200),
    # tc
    ('tc', '01-XD', '크로스도킹', 40, 1500, 1500),
    # dc
    ('dc', '01-IB', '입고', 40, 800, 800),
    ('dc', '02-ST', '보관', 100, 2000, 2000),
    ('dc', '03-PK', '피킹', 80, 1500, 1500),
    ('dc', '04-OB', '출고', 40, 800, 800),
    # megaFc
    ('megaFc', '01-IB', '입고', 40, 800, 800),
    ('megaFc', '02-IS', '검수', 40, 600, 600),
    ('megaFc', '03-ST', '랙 보관', 200, 3000, 3000),
    ('megaFc', '04-PK', '피킹', 120, 2000, 2000),
    ('megaFc', '05-PC', '가공', 30, 1000, 1000),
    ('megaFc', '06-SR', '분류', 80, 1500, 1500),
    ('megaFc', '07-OB', '출고', 40, 1200, 1200),
    # superFc
    ('superFc', '01-IB', '입고', 60, 1000, 1000),
    ('superFc', '02-IS', '검수', 60, 800, 800),
    ('superFc', '03-ST', '대형 랙 보관', 400, 4000, 4000),
    ('superFc', '04-PK', '자동 피킹', 200, 3000, 3000),
    ('superFc', '05-PC', '가공/재작업', 50, 1500, 1500),
    ('superFc', '06-SR', '지능형 분류', 150, 2000, 2000),
    ('superFc', '07-OB', '출고/배송', 80, 2000, 2000),
    ('superFc', '08-RET', '반품 처리', 40, 1000, 1000),
    # intlHub
    ('intlHub', '01-IB', '국제 입고', 100, 2000, 2000),
    ('intlHub', '02-CS', '통관/검사', 80, 1500, 1500),
    ('intlHub', '03-SR', '국제 분류', 200, 2500, 2500),
    ('intlHub', '04-EX', '수출 처리', 120, 2000, 2000),
    ('intlHub', '05-OB', '국제 출고', 80, 1500, 1500),
    # autoFc
    ('autoFc', '01-SR', '자동 분류', 300, 3000, 3000),
    ('autoFc', '02-PK', '로봇 피킹', 250, 2500, 2500),
    ('autoFc', '03-RB', '로봇 팔 처리', 100, 2000, 2000),
    ('autoFc', '04-OB', '자동 출고', 150, 2000, 2000)
]

for preset_key, zone_id, zone_name, lines, length, sensors in preset_zones_data:
    cursor.execute(
        'INSERT INTO preset_zones (preset_key, zone_id, zone_name, lines, length, sensors) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING',
        (preset_key, zone_id, zone_name, lines, length, sensors)
    )

conn.commit()
cursor.close()
conn.close()

print('✅ 프리셋 데이터 삽입 완료')
