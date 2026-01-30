import axios from 'axios';

// API 베이스 URL - Azure VM의 백엔드 서버 주소
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://20.196.224.42:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// API 엔드포인트
export const apiService = {
  // 헬스 체크
  getHealth: async () => {
    const response = await api.get('/');
    return response.data;
  },

  // 최신 센서 이벤트 조회
  getLatestSensors: async (zoneId = null, limit = 10) => {
    const response = await api.get('/events/latest', { params: { count: limit } });
    return response.data;
  },

  // 센서 히스토리 조회 - 원본 센서 데이터
  getSensorHistory: async (zoneId = null, limit = 100) => {
    const params = {};
    if (zoneId) params.zone_id = zoneId;
    if (limit) params.count = limit;
    const response = await api.get('/sensors/history', { params });
    return response.data;
  },

  // Zone별 요약 정보 (통계에서 추출)
  getZonesSummary: async (hours = 1) => {
    const response = await api.get('/zones/summary');
    return response.data;
  },

  // ========== ZONES 설정 API ==========
  // zones 설정 조회
  getZonesConfig: async () => {
    const response = await api.get('/zones/config');
    return response.data;
  },

  // zone 추가 (구엔드포인트 - 호환성)
  createZone: async (zone) => {
    const response = await api.post('/zones/config', zone);
    return response.data;
  },

  // 존 생성 (신규 엔드포인트)
  createZone: async (zone) => {
    const response = await api.post('/zones', zone);
    return response.data;
  },

  // 라인 저장 (신규)
  createLines: async (lines) => {
    const response = await api.post('/lines', lines);
    return response.data;
  },

  // zone 업데이트
  updateZone: async (zoneId, zone) => {
    const response = await api.put(`/zones/config/${zoneId}`, zone);
    return response.data;
  },

  // zone 삭제
  deleteZone: async (zoneId) => {
    const response = await api.delete(`/zones/config/${zoneId}`);
    return response.data;
  },

  // zones 전체 설정 (일괄 저장)
  setZonesBatch: async (zones) => {
    const response = await api.post('/zones/config/batch', zones);
    return response.data;
  },

  // 병목 현상 감지
  getBottlenecks: async (hours = 1) => {
    const response = await api.get('/bottlenecks');
    return Array.isArray(response.data) ? response.data : [];
  },

  // 시뮬레이션 파라미터 조회 (임시)
  getSimulationParams: async () => {
    return { signal_probability: 0.6, speed_percent: 50 };
  },

  // 시뮬레이션 파라미터 업데이트 (임시)
  updateSimulationParams: async (params) => {
    return { success: true, params };
  },

  // 센서 시뮬레이션 시작
  startSimulation: async () => {
    try {
      const response = await api.post('/simulator/start');
      return response.data;
    } catch (error) {
      console.error('시뮬레이션 시작 오류:', error);
      throw error;
    }
  },

  // 센서 시뮬레이션 중지
  stopSimulation: async () => {
    try {
      const response = await api.post('/simulator/stop');
      return response.data;
    } catch (error) {
      console.error('시뮬레이션 중지 오류:', error);
      throw error;
    }
  },

  // 센서 시뮬레이션 상태 조회
  getSimulationStatus: async () => {
    try {
      const response = await api.get('/simulator/status');
      return response.data;
    } catch (error) {
      console.error('시뮬레이션 상태 조회 오류:', error);
      return { running: false };
    }
  },

  // ========== 프리셋 API ==========
  
  // 모든 프리셋 목록 조회
  getPresets: async () => {
    try {
      const response = await api.get('/presets');
      return response.data;
    } catch (error) {
      console.error('프리셋 목록 조회 오류:', error);
      throw error;
    }
  },

  // 특정 프리셋 상세 조회
  getPresetDetail: async (presetKey) => {
    try {
      const response = await api.get(`/presets/${presetKey}`);
      return response.data;
    } catch (error) {
      console.error(`프리셋 ${presetKey} 조회 오류:`, error);
      throw error;
    }
  },

  // 프리셋 적용 (zones/lines 교체)
  applyPreset: async (presetKey) => {
    try {
      const response = await api.post(`/presets/${presetKey}/apply`);
      return response.data;
    } catch (error) {
      console.error(`프리셋 ${presetKey} 적용 오류:`, error);
      throw error;
    }
  }
};

export default api;
