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
    const response = await api.get('/api/health');
    return response.data;
  },

  // 최신 센서 데이터 조회
  getLatestSensors: async (zoneId = null, limit = 100) => {
    const params = { limit };
    if (zoneId) params.zone_id = zoneId;
    const response = await api.get('/api/sensors/latest', { params });
    return response.data;
  },

  // 센서 히스토리 조회
  getSensorHistory: async (zoneId = null, aggregatedId = null, hours = 24, limit = 500) => {
    const params = { hours, limit };
    if (zoneId) params.zone_id = zoneId;
    if (aggregatedId) params.aggregated_id = aggregatedId;
    const response = await api.get('/api/sensors/history', { params });
    return response.data;
  },

  // Zone별 요약 정보
  getZonesSummary: async (hours = 1) => {
    const response = await api.get('/api/zones/summary', { params: { hours } });
    return response.data;
  },

  // 병목 현상 감지
  getBottlenecks: async (hours = 1) => {
    const response = await api.get('/api/bottlenecks', { params: { hours } });
    return response.data;  },

  // 시뮬레이션 파라미터 조회
  getSimulationParams: async () => {
    const response = await api.get('/api/simulation/params');
    return response.data;
  },

  // 시뮬레이션 파라미터 업데이트
  updateSimulationParams: async (params) => {
    const response = await api.post('/api/simulation/params', params);
    return response.data;  }
};

export default api;
