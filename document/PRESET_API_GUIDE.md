"""
프리셋 API 추가 가이드

현재 상태:
- ✅ 프론트엔드: 프리셋 정의 및 UI 연동 완료
- ✅ DB 스크립트: init_presets.py 생성 완료
- ❌ 백엔드 API: 프리셋 조회/적용 API 없음

필요한 작업:
1. backend_main.py에 프리셋 API 추가
2. 프론트엔드와 연동 테스트
"""

# =============================================
# backend_main.py에 추가할 코드
# =============================================

# [1] 프리셋 목록 조회
@app.get("/presets", tags=["Presets"])
async def get_all_presets():
    """
    모든 센터 프리셋 목록 조회
    
    Returns:
        - preset_key: 프리셋 키
        - preset_name: 센터명
        - total_zones: Zone 개수
        - total_lines: 총 라인 수
        - total_sensors: 총 센서 수
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT preset_key, preset_name, description,
                           total_zones, total_lines, total_length_m, total_sensors
                    FROM facility_presets
                    ORDER BY total_lines DESC
                """)
                
                presets = []
                for row in cur.fetchall():
                    presets.append({
                        'preset_key': row[0],
                        'preset_name': row[1],
                        'description': row[2],
                        'total_zones': row[3],
                        'total_lines': row[4],
                        'total_length_m': row[5],
                        'total_sensors': row[6]
                    })
                
                return {'presets': presets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프리셋 조회 실패: {str(e)}")


# [2] 특정 프리셋 상세 조회
@app.get("/presets/{preset_key}", tags=["Presets"])
async def get_preset_detail(preset_key: str):
    """
    특정 프리셋의 Zone 상세 정보 조회
    
    Args:
        preset_key: 프리셋 키 (mfc, dc, megaFc, superFc 등)
    
    Returns:
        - preset_info: 프리셋 메타데이터
        - zones: Zone별 상세 정보
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 프리셋 기본 정보
                cur.execute("""
                    SELECT preset_name, description, total_zones, total_lines, 
                           total_length_m, total_sensors
                    FROM facility_presets
                    WHERE preset_key = %s
                """, (preset_key,))
                
                preset_row = cur.fetchone()
                if not preset_row:
                    raise HTTPException(status_code=404, detail=f"프리셋 '{preset_key}'를 찾을 수 없습니다")
                
                preset_info = {
                    'preset_key': preset_key,
                    'preset_name': preset_row[0],
                    'description': preset_row[1],
                    'total_zones': preset_row[2],
                    'total_lines': preset_row[3],
                    'total_length_m': preset_row[4],
                    'total_sensors': preset_row[5]
                }
                
                # Zone 상세 정보
                cur.execute("""
                    SELECT zone_id, zone_name, lines, length_m, sensors, zone_order
                    FROM preset_zones
                    WHERE preset_key = %s
                    ORDER BY zone_order
                """, (preset_key,))
                
                zones = []
                for row in cur.fetchall():
                    zones.append({
                        'id': row[0],         # frontend 형식 맞춤 (zone_id → id)
                        'name': row[1],
                        'lines': row[2],
                        'length': row[3],
                        'sensors': row[4]
                    })
                
                return {
                    'preset_info': preset_info,
                    'zones': zones
                }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프리셋 상세 조회 실패: {str(e)}")


# [3] 프리셋 적용 (기존 zones 교체)
@app.post("/presets/{preset_key}/apply", tags=["Presets"])
async def apply_preset(preset_key: str):
    """
    프리셋을 현재 시스템에 적용 (기존 zones 교체)
    
    Args:
        preset_key: 적용할 프리셋 키
    
    Returns:
        - message: 성공 메시지
        - zones: 적용된 Zone 목록
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 프리셋 존재 확인
                cur.execute("SELECT 1 FROM facility_presets WHERE preset_key = %s", (preset_key,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail=f"프리셋 '{preset_key}'를 찾을 수 없습니다")
                
                # 기존 zones 및 lines 삭제
                cur.execute("DELETE FROM logistics_lines")
                cur.execute("DELETE FROM logistics_zones")
                
                # 프리셋에서 zones 복사
                cur.execute("""
                    SELECT zone_id, zone_name, zone_order
                    FROM preset_zones
                    WHERE preset_key = %s
                    ORDER BY zone_order
                """, (preset_key,))
                
                zones = cur.fetchall()
                applied_zones = []
                
                for zone_row in zones:
                    zone_id, zone_name, zone_order = zone_row
                    
                    # Zone 삽입
                    cur.execute("""
                        INSERT INTO logistics_zones 
                        (zone_id, zone_name, description, location_x, location_y, size_width, size_height)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (zone_id, zone_name, f'{zone_name} (프리셋 적용)', 
                          100 + zone_order * 250, 100, 200, 150))
                    
                    # Zone의 lines 정보 가져오기
                    cur.execute("""
                        SELECT lines, length_m
                        FROM preset_zones
                        WHERE preset_key = %s AND zone_id = %s
                    """, (preset_key, zone_id))
                    
                    line_info = cur.fetchone()
                    if line_info:
                        num_lines, line_length = line_info
                        
                        # Lines 생성
                        for i in range(num_lines):
                            line_id = f"{zone_id}-{i+1:03d}"
                            cur.execute("""
                                INSERT INTO logistics_lines
                                (line_id, line_name, zone_id, start_point_x, start_point_y,
                                 end_point_x, end_point_y, length_meters, speed_limit_kmh, priority)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (line_id, f"라인 {i+1}", zone_id,
                                  100, 100 + i * 30, 100 + line_length, 100 + i * 30,
                                  line_length, 20, i+1))
                        
                        applied_zones.append({
                            'zone_id': zone_id,
                            'zone_name': zone_name,
                            'lines_created': num_lines
                        })
                
                conn.commit()
                
                return {
                    'message': f"프리셋 '{preset_key}' 적용 완료",
                    'zones_created': len(applied_zones),
                    'zones': applied_zones
                }
    
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"프리셋 적용 실패: {str(e)}")


# =============================================
# 사용 방법
# =============================================

"""
1. 프리셋 DB 초기화:
   python init_presets.py

2. 백엔드 API 추가:
   위 코드를 backend_main.py에 복사

3. 프론트엔드에서 사용:
   - GET /presets → 프리셋 목록 조회
   - GET /presets/superFc → 특정 프리셋 상세
   - POST /presets/superFc/apply → 프리셋 적용

4. 프론트엔드 api.js 수정:
   
   // 프리셋 API 추가
   getPresets: async () => {
     const response = await api.get('/presets');
     return response.data;
   },
   
   getPresetDetail: async (presetKey) => {
     const response = await api.get(`/presets/${presetKey}`);
     return response.data;
   },
   
   applyPreset: async (presetKey) => {
     const response = await api.post(`/presets/${presetKey}/apply`);
     return response.data;
   }

5. LogisticsRailSettingPage.jsx 수정:
   
   const handlePresetClick = async (presetKey) => {
     if (!window.confirm('물류센터 시설정보가 변경됩니다. 확인하시겠습니까?')) {
       return;
     }
     
     try {
       // 백엔드 프리셋 API 사용
       const result = await apiService.applyPreset(presetKey);
       console.log(result.message);
       
       // Zone 목록 새로고침
       await loadZones();
       
     } catch (error) {
       console.error('프리셋 로드 중 오류:', error);
       alert('프리셋 적용 실패');
     }
   };
"""
