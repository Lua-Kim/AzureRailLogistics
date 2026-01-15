import React, { useState, useEffect } from 'react';
import styled, { keyframes } from 'styled-components';
import { useLocation } from 'react-router-dom';
import { 
  BarChart3, Activity, Repeat, Zap, Cpu, Clock, 
  ChevronRight, Circle, LayoutDashboard, Loader2, AlertTriangle 
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
  const { zoneId, zoneName } = location.state || { zoneId: null, zoneName: 'Unknown Zone' };
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sensorData, setSensorData] = useState([]);
  const [metrics, setMetrics] = useState({
    tph: 0, congestion: 0, recirculation: 0, efficiency: 0, oee: 0, bottleneck: 0
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        if (!zoneId) {
          setError('Zone ID가 선택되지 않았습니다');
          setLoading(false);
          return;
        }
        
        const historyData = await apiService.getSensorHistory(zoneId, 20);
        setSensorData(historyData);
        
        if (historyData.length > 0) {
          const latest = historyData[0];
          const avgThroughput = historyData.reduce((sum, d) => sum + d.item_throughput, 0) / historyData.length;
          const avgSpeed = historyData.reduce((sum, d) => sum + d.avg_speed, 0) / historyData.length;
          
          setMetrics({
            tph: Math.round(avgThroughput),
            congestion: Math.round(100 - avgSpeed),
            recirculation: latest.bottleneck_indicator?.recirculation_rate || 0,
            efficiency: Math.round(avgSpeed),
            oee: Math.round(avgSpeed * 0.85),
            bottleneck: latest.bottleneck_indicator?.bottleneck_score || 0
          });
        }
      } catch (err) {
        console.error('Failed to fetch zone analytics:', err);
        setError('데이터를 불러오는데 실패했습니다');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [zoneId]);

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

  // 라인별 센서 그룹화
  const groupBySensorLine = () => {
    const grouped = {};
    sensorData.forEach(sensor => {
      if (!grouped[sensor.line_direction]) {
        grouped[sensor.line_direction] = [];
      }
      grouped[sensor.line_direction].push(sensor);
    });
    return grouped;
  };

  // 색상 결정 함수 (물동량과 속도 기반)
  const getSensorColor = (throughput, speed) => {
    if (throughput === 0) return '#6b7280'; // 오프라인
    if (speed < 1.0) return '#ef4444'; // 병목 - 빨강 (거의 정지)
    if (speed < 2.0) return '#fbbf24'; // 주의 - 노랑 (저속)
    return '#10b981'; // 정상 - 초록 (정상 속도)
  };

  const sensorsByLine = groupBySensorLine();

  return (
    <PageContainer>
      {/* 라인 시각화 */}
      <LineVisualizationContainer>
        <LineTitle>
          <Activity size={16} />
          {zoneId} 라인별 센서 상태
        </LineTitle>
        <LineFlowVisualization>
          {Object.entries(sensorsByLine).map(([line, sensors]) => (
            <LineRow key={line}>
              <LineLabel>{line}</LineLabel>
              <SensorLine>
                {sensors.map((sensor, idx) => {
                  const color = getSensorColor(sensor.item_throughput, sensor.avg_speed);
                  const isPulse = color === '#ef4444'; // 병목 센서는 애니메이션
                  return (
                    <SensorNode
                      key={idx}
                      color={color}
                      pulse={isPulse}
                      title={`${sensor.aggregated_id}\n물동량: ${sensor.item_throughput}\n속도: ${sensor.avg_speed.toFixed(2)}`}
                    >
                      {idx + 1}
                    </SensorNode>
                  );
                })}
              </SensorLine>
            </LineRow>
          ))}
        </LineFlowVisualization>
        
        {/* 범례 */}
        <div style={{ display: 'flex', gap: '24px', marginTop: '24px', paddingTop: '24px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#10b981' }} />
            <span style={{ fontSize: '11px', color: '#9ca3af' }}>정상 (속도 2.5↑)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#fbbf24' }} />
            <span style={{ fontSize: '11px', color: '#9ca3af' }}>주의 (속도 1.5~2.5)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ef4444' }} />
            <span style={{ fontSize: '11px', color: '#9ca3af' }}>병목 (속도 1.5↓)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#6b7280' }} />
            <span style={{ fontSize: '11px', color: '#9ca3af' }}>오프라인</span>
          </div>
        </div>
      </LineVisualizationContainer>

      {/* 1. Header Section */}
      <TopHeader>
        <TitleSection>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <h2>Logistics Zone <span>ANALYTICS</span></h2>
            <ZoneBadge>{zoneName || zoneId}</ZoneBadge>
          </div>
          <p>{zoneId} | OPERATIONAL COST FOCUS</p>
        </TitleSection>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'inherit', padding: '8px 16px', borderRadius: '20px', border: `1px solid ${'#1e293b'}` }}>
            <Circle size={8} fill="#10b981" color="#10b981" />
            <span style={{ fontSize: '10px', fontWeight: 900, color: 'inherit' }}>LIVE: ANALYTICS ACTIVE</span>
          </div>
          <LossCard>
            <h4>TARGET ZONE LOSS ESTIMATE</h4>
            <p>₩{(metrics.bottleneck * 58.4).toLocaleString()}</p>
          </LossCard>
        </div>
      </TopHeader>

      {/* 2. KPI Metrics Grid */}
      <MetricsGrid>
        <MetricCard>
          <MetricHeader><span style={{ color: 'inherit' }}>TPH (Throughput)</span><BarChart3 size={18} /></MetricHeader>
          <MetricValue>
            <h3>{metrics.tph}</h3>
            <p>Units/hr</p>
          </MetricValue>
        </MetricCard>
        <MetricCard>
          <MetricHeader><span style={{ color: 'inherit' }}>Congestion Index</span><Activity size={18} color="#fbbf24" /></MetricHeader>
          <MetricValue>
            <h3>{metrics.congestion}%</h3>
            <p>Density</p>
          </MetricValue>
        </MetricCard>
        <MetricCard>
          <MetricHeader><span style={{ color: 'inherit' }}>Recirculation</span><Repeat size={18} color="#10b981" /></MetricHeader>
          <MetricValue>
            <h3>{metrics.recirculation}%</h3>
            <p>Loop Rate</p>
          </MetricValue>
        </MetricCard>
        <MetricCard>
          <MetricHeader><span style={{ color: 'inherit' }}>Energy Efficiency</span><Zap size={18} /></MetricHeader>
          <MetricValue>
            <h3>{metrics.efficiency}%</h3>
            <p>kW/Load</p>
          </MetricValue>
        </MetricCard>
        <MetricCard>
          <MetricHeader><span style={{ color: 'inherit' }}>OEE Status</span><Cpu size={18} color="#10b981" /></MetricHeader>
          <MetricValue>
            <h3>{metrics.oee}%</h3>
            <p>Health</p>
          </MetricValue>
        </MetricCard>
      </MetricsGrid>

      {/* 3. Visualizations */}
      <VisualizationRow style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* 시간대별 처리량 */}
        <ChartContainer>
          <ChartTitle><BarChart3 size={14} /> 시간대별 처리량 추이</ChartTitle>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={sensorData.map((d, i) => ({
              time: `${i}s`,
              throughput: d.item_throughput
            }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="time" stroke="rgba(255,255,255,0.5)" />
              <YAxis stroke="rgba(255,255,255,0.5)" />
              <Tooltip 
                contentStyle={{ background: 'rgba(0,0,0,0.8)', border: '1px solid #3b82f6' }}
                labelStyle={{ color: '#fff' }}
              />
              <Line type="monotone" dataKey="throughput" stroke="#3b82f6" isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
        
        {/* 시간대별 평균 속도 */}
        <ChartContainer>
          <ChartTitle><Activity size={14} /> 시간대별 평균 속도</ChartTitle>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={sensorData.map((d, i) => ({
              time: `${i}s`,
              speed: d.avg_speed
            }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="time" stroke="rgba(255,255,255,0.5)" />
              <YAxis stroke="rgba(255,255,255,0.5)" />
              <Tooltip 
                contentStyle={{ background: 'rgba(0,0,0,0.8)', border: '1px solid #10b981' }}
                labelStyle={{ color: '#fff' }}
              />
              <Line type="monotone" dataKey="speed" stroke="#10b981" isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </VisualizationRow>

      {/* 센서 상태 분포 및 병목 스코어 */}
      <VisualizationRow style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* 센서 상태 분포 */}
        <ChartContainer>
          <ChartTitle><Cpu size={14} /> 센서 상태 분포</ChartTitle>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={sensorData.length > 0 ? [
                  { name: '정상', value: sensorData[0].sensor_status_breakdown?.정상 || 0, fill: '#10b981' },
                  { name: '경고', value: sensorData[0].sensor_status_breakdown?.경고 || 0, fill: '#fbbf24' },
                  { name: '오류', value: sensorData[0].sensor_status_breakdown?.오류 || 0, fill: '#ef4444' },
                  { name: '오프라인', value: sensorData[0].sensor_status_breakdown?.오프라인 || 0, fill: '#6b7280' }
                ] : []}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={5}
                dataKey="value"
              >
                {sensorData.length > 0 && [
                  { name: '정상', value: sensorData[0].sensor_status_breakdown?.정상 || 0, fill: '#10b981' },
                  { name: '경고', value: sensorData[0].sensor_status_breakdown?.경고 || 0, fill: '#fbbf24' },
                  { name: '오류', value: sensorData[0].sensor_status_breakdown?.오류 || 0, fill: '#ef4444' },
                  { name: '오프라인', value: sensorData[0].sensor_status_breakdown?.오프라인 || 0, fill: '#6b7280' }
                ].map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ background: 'rgba(0,0,0,0.8)', border: '1px solid #3b82f6' }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartContainer>

        {/* 병목 스코어 추이 */}
        <ChartContainer>
          <ChartTitle><AlertTriangle size={14} /> 병목 스코어 추이</ChartTitle>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={sensorData.map((d, i) => ({
              time: `${i}s`,
              bottleneck: (d.bottleneck_indicator?.bottleneck_score || 0) * 100
            }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="time" stroke="rgba(255,255,255,0.5)" />
              <YAxis stroke="rgba(255,255,255,0.5)" />
              <Tooltip 
                contentStyle={{ background: 'rgba(0,0,0,0.8)', border: '1px solid #ef4444' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="bottleneck" fill="#ef4444" isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </VisualizationRow>
    </PageContainer>
  );
};

export default MicroPage;