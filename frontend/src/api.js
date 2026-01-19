import axios from 'axios';

// API 베이스 URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
  }
};

export default api;
