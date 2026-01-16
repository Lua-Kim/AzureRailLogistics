import React, { useState, useEffect, useRef } from 'react';
import styled, { keyframes } from 'styled-components';
import { useLocation } from 'react-router-dom';
import { 
  BarChart3, Activity, Repeat, Zap, Cpu, Clock, 
  ChevronRight, Circle, LayoutDashboard, Loader2, AlertTriangle, TrendingUp
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiService } from './api';

// --- [Animations] ---
const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
`;

// --- [Styled Components] ---
const PageContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 32px;
  animation: ${fadeIn} 0.6s ease-out;
  color: ${props => props.theme.colors.text.main};
`;

const TopHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
`;

const TitleSection = styled.div`
  h2 {
    font-size: 32px;
    font-weight: 900;
    margin: 0;
    color: ${props => props.theme.colors.text.main};
    span { color: ${props => props.theme.colors.primary}; }
  }
  p {
    font-size: 12px;
    font-weight: 700;
    color: ${props => props.theme.colors.text.muted};
    letter-spacing: 0.2em;
    margin-top: 8px;
  }
`;

const LossCard = styled.div`
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  padding: 20px 32px;
  border-radius: 16px;
  text-align: right;
  h4 { color: ${props => props.theme.colors.status.danger}; font-size: 10px; font-weight: 900; margin: 0 0 8px; }
  p { color: ${props => props.theme.colors.status.danger}; font-size: 28px; font-weight: 900; margin: 0; font-family: 'monospace'; }
`;

const ZoneBadge = styled.span`
  background-color: rgba(59, 130, 246, 0.15);
  color: ${props => props.theme.colors.primary};
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.05em;
  margin-left: 20px;
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
`;

const MetricCard = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 16px;
  padding: 24px;
  position: relative;
  transition: border-color 0.3s;
  &:hover { border-color: ${props => props.theme.colors.primary}; }
`;

const MetricHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  span { font-size: 11px; font-weight: 800; color: ${props => props.theme.colors.text.muted}; }
  svg { color: ${props => props.color || props.theme.colors.primary}; opacity: 0.8; }
`;

const MetricValue = styled.div`
  h3 { font-size: 24px; font-weight: 900; margin: 0; color: ${props => props.theme.colors.text.main}; }
  p { font-size: 10px; color: ${props => props.theme.colors.text.muted}; margin-top: 4px; font-weight: 700; }
`;

const VisualizationRow = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
`;

const ChartContainer = styled.div`
  background: ${props => props.theme.colors.surfaceTransparent};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 24px;
  padding: 24px;
  display: flex;
  flex-direction: column;
`;

const ChartTitle = styled.div`
  font-size: 11px;
  font-weight: 900;
  color: ${props => props.theme.colors.text.muted};
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
`;

const SensorGrid = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 0;
`;

// 라인 시각화 스타일
const LineVisualizationContainer = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 20px;
  padding: 32px;
  margin-bottom: 32px;
  animation: ${fadeIn} 0.6s ease-out;
`;

const LineTitle = styled.div`
  font-size: 12px;
  font-weight: 900;
  color: ${props => props.theme.colors.text.muted};
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const LineFlowVisualization = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const LineRow = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

const LineLabel = styled.div`
  width: 120px;
  font-size: 12px;
  font-weight: 800;
  color: ${props => props.theme.colors.text.main};
  white-space: nowrap;
`;

const SensorLine = styled.div`
  flex: 1;
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 12px;
  background: rgba(59, 130, 246, 0.05);
  border-radius: 12px;
  overflow-x: auto;
  
  &::-webkit-scrollbar {
    height: 4px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.3);
    border-radius: 2px;
  }
`;

const SensorNode = styled.div`
  min-width: 40px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: ${props => props.color || '#3b82f6'};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: white;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px ${props => props.color || '#3b82f6'}66;
  border: 2px solid ${props => props.color || '#3b82f6'};
  
  &:hover {
    transform: scale(1.15);
    box-shadow: 0 4px 16px ${props => props.color || '#3b82f6'}99;
  }
  
  animation: ${props => props.pulse ? 'pulse 2s infinite' : 'none'};
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }
`;

const SensorTooltip = styled.div`
  position: absolute;
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 10px;
  white-space: nowrap;
  z-index: 10;
  border: 1px solid ${props => props.theme.colors.primary};
  pointer-events: none;
`;

const SensorRow = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  span { font-size: 12px; font-weight: 900; color: ${props => props.theme.colors.text.muted}; width: 24px; }
`;

const GridBox = styled.div`
  flex: 1;
  height: 32px;
  background: ${props => props.active ? 'rgba(59, 130, 246, 0.5)' : props.theme.colors.border};
  border-radius: 4px;
  border: 1px solid ${props => props.theme.colors.surface};
`;

// --- [Main Component] ---
const MicroPage = () => {
  const location = useLocation();
  const { zoneId, zoneName, sensorCount } = location.state || { 
    zoneId: 'IB-01',  // 기본값: 입고(INBOUND)
    zoneName: '입고', 
    sensorCount: 40 
  };
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sensorData, setSensorData] = useState([]);
  const [metrics, setMetrics] = useState({
    tph: 0, congestion: 0, recirculation: 0, efficiency: 0, oee: 0, bottleneck: 0
  });
  const isInitialLoad = useRef(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (isInitialLoad.current) {
          setLoading(true); // 초회 로드에서만 로딩 스피너 표시
        }
        setError(null);
        
        const historyData = await apiService.getSensorHistory(zoneId, sensorCount);
        
        // 응답이 배열인지 확인, 아니면 빈 배열로 설정
        const dataArray = Array.isArray(historyData) ? historyData : [];
        setSensorData(dataArray.slice(-sensorCount));
        
        if (dataArray.length > 0) {
          // 원본 센서 데이터에서 metrics 계산
          const activeEvents = dataArray.filter(e => e.signal);
          const avgSpeed = activeEvents.length > 0
            ? activeEvents.reduce((sum, e) => sum + e.speed, 0) / activeEvents.length
            : 0;
          
          setMetrics({
            tph: activeEvents.length,
            congestion: Math.round(100 - avgSpeed),
            recirculation: 0,
            efficiency: Math.round(avgSpeed),
            oee: Math.round(avgSpeed * 0.85),
            bottleneck: dataArray.filter(e => e.speed < 30).length
          });
        }
      } catch (err) {
        console.error('Failed to fetch zone analytics:', err);
        setError('데이터를 불러오는데 실패했습니다');
      } finally {
        if (isInitialLoad.current) {
          isInitialLoad.current = false;
          setLoading(false);
        }
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [zoneId, sensorCount]);

  if (loading) {
    return (
      <PageContainer>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
          <Loader2 size={48} className="animate-spin" color="#3b82f6" />
        </div>
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100vh', gap: '16px' }}>
          <AlertTriangle size={48} color="#ef4444" />
          <p style={{ fontSize: '18px', color: '#ef4444' }}>{error}</p>
        </div>
      </PageContainer>
    );
  }

  // 라인별 센서 데이터 그룹화 - 실시간 센서 이벤트를 라인별로 정렬
  const groupSensorDataByLine = () => {
    const grouped = {};
    
    if (!Array.isArray(sensorData)) {
      return {};
    }
    
    // line_id별로 이벤트를 그룹화
    sensorData.forEach((event) => {
      const lineId = event.line_id || 'LINE-1';
      if (!grouped[lineId]) {
        grouped[lineId] = [];
      }
      grouped[lineId].push({
        timestamp: event.timestamp,
        speed: event.speed ?? 0,
        signal: event.signal,
        sensor_id: event.sensor_id || 'sensor-unk'
      });
    });
    
    return grouped;
  };

  // 라인별 속도 그래프 데이터 생성
  const getLineSpeedChartData = (lineEvents) => {
    return lineEvents.map((event, idx) => ({
      time: idx,
      speed: event.speed,
      sensor: event.sensor_id ? event.sensor_id.substring(event.sensor_id.length - 5) : 'UNK'
    }));
  };

  const sensorsByLine = groupSensorDataByLine();
  const hasLineCharts = Object.keys(sensorsByLine).length > 0;
  const fallbackLineData = sensorData.map((event, idx) => ({
    time: idx,
    speed: event.speed ?? 0,
    sensor: event.sensor_id ? event.sensor_id.substring(event.sensor_id.length - 5) : 'UNK'
  }));

  return (
    <PageContainer>
      {/* 1. Header Section */}
      <TopHeader>
        <TitleSection>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <h2>Logistics Zone <span>ANALYTICS</span></h2>
            <ZoneBadge>{zoneName || zoneId}</ZoneBadge>
          </div>
          <p>{zoneId} | REAL-TIME SENSOR DATA</p>
        </TitleSection>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'inherit', padding: '8px 16px', borderRadius: '20px', border: `1px solid #1e293b` }}>
            <Circle size={8} fill="#10b981" color="#10b981" />
            <span style={{ fontSize: '10px', fontWeight: 900, color: 'inherit' }}>LIVE: {sensorData.length} EVENTS</span>
          </div>
        </div>
      </TopHeader>

      {/* 2. KPI Metrics Grid */}
      <MetricsGrid>
        <MetricCard>
          <MetricHeader><span style={{ color: 'inherit' }}>Total Events</span><BarChart3 size={18} /></MetricHeader>
          <MetricValue>
            <h3>{sensorData.length}</h3>
            <p>Received</p>
          </MetricValue>
        </MetricCard>
        <MetricCard>
          <MetricHeader><span style={{ color: 'inherit' }}>Active Lines</span><Activity size={18} color="#fbbf24" /></MetricHeader>
          <MetricValue>
            <h3>{Object.keys(sensorsByLine).length}</h3>
            <p>Lines</p>
          </MetricValue>
        </MetricCard>
        <MetricCard>
          <MetricHeader><span style={{ color: 'inherit' }}>Avg Speed</span><Repeat size={18} color="#10b981" /></MetricHeader>
          <MetricValue>
            <h3>{metrics.efficiency}%</h3>
            <p>Speed</p>
          </MetricValue>
        </MetricCard>
        <MetricCard>
          <MetricHeader><span style={{ color: 'inherit' }}>Signal True</span><Zap size={18} /></MetricHeader>
          <MetricValue>
            <h3>{sensorData.filter(e => e.signal).length}</h3>
            <p>Active</p>
          </MetricValue>
        </MetricCard>
        <MetricCard>
          <MetricHeader><span style={{ color: 'inherit' }}>Bottleneck</span><Cpu size={18} color="#ef4444" /></MetricHeader>
          <MetricValue>
            <h3>{metrics.bottleneck}</h3>
            <p>Events</p>
          </MetricValue>
        </MetricCard>
      </MetricsGrid>

      {/* 3. 라인별 속도 그래프 */}
      <VisualizationRow>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {Object.entries(sensorsByLine).map(([lineId, events]) => (
            <ChartContainer key={lineId}>
              <ChartTitle>
                <TrendingUp size={14} />
                {lineId} - 속도 데이터 ({events.length} events)
              </ChartTitle>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={getLineSpeedChartData(events)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis 
                    dataKey="time" 
                    stroke="rgba(255,255,255,0.5)"
                    label={{ value: 'Event Index', position: 'insideBottomRight', offset: -5 }}
                  />
                  <YAxis 
                    stroke="rgba(255,255,255,0.5)"
                    label={{ value: 'Speed (%)', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip 
                    contentStyle={{ background: 'rgba(0,0,0,0.9)', border: '1px solid #3b82f6' }}
                    labelStyle={{ color: '#fff' }}
                    formatter={(value) => `${value}%`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="speed" 
                    stroke="#3b82f6" 
                    isAnimationActive={true}
                    animationDuration={300}
                    dot={{ r: 3 }}
                    name="Speed"
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>
          ))}
        </div>
      </VisualizationRow>

      {/* 4. 센서 이벤트 요약 */}
      <VisualizationRow style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <ChartContainer>
          <ChartTitle><Activity size={14} /> 신호 분포</ChartTitle>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={[
              { name: 'Signal True', value: sensorData.filter(e => e.signal).length, fill: '#10b981' },
              { name: 'Signal False', value: sensorData.filter(e => !e.signal).length, fill: '#ef4444' }
            ]}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" />
              <YAxis stroke="rgba(255,255,255,0.5)" />
              <Tooltip contentStyle={{ background: 'rgba(0,0,0,0.8)', border: '1px solid #3b82f6' }} />
              <Bar dataKey="value" fill="#3b82f6" isAnimationActive={true} animationDuration={300} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>

        <ChartContainer>
          <ChartTitle><Clock size={14} /> 최근 이벤트 목록</ChartTitle>
          <div style={{ fontSize: '11px', color: '#9ca3af', maxHeight: '200px', overflowY: 'auto' }}>
            {sensorData.slice(0, 10).map((event, idx) => (
              <div key={idx} style={{ padding: '8px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <div style={{ fontWeight: 700, color: '#fff' }}>
                  {event.sensor_id.substring(event.sensor_id.length - 5)}
                </div>
                <div>
                  Speed: <span style={{ color: '#3b82f6' }}>{event.speed}%</span>
                  {' | '} 
                  Signal: <span style={{ color: event.signal ? '#10b981' : '#ef4444' }}>
                    {event.signal ? 'ON' : 'OFF'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </ChartContainer>
      </VisualizationRow>
    </PageContainer>
  );
};

export default MicroPage;