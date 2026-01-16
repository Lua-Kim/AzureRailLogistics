import React, { useState, useEffect, useMemo, useCallback } from 'react';
import styled, { keyframes, css } from 'styled-components';
import { useNavigate } from 'react-router-dom';
import { 
  ShoppingCart, RotateCcw, Truck, TrendingDown, Thermometer, Wind, Users, Cpu, ChevronRight,
  BarChart3, Zap, Circle, BrainCircuit, Loader2, AlertTriangle, Activity
} from 'lucide-react';
import { apiService } from './api';

// 센서 구성 (메가FC 기준)
const ZONE_SENSOR_CONFIG = {
  'IB-01': 40,   // 입고
  'IS-01': 50,   // 검수
  'ST-RC': 300,  // 랙 보관
  'PK-01': 200,  // 피킹
  'PC-01': 50,   // 가공
  'SR-01': 160,  // 분류
  'OB-01': 40    // 출고
};

// --- [Animations] ---
const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
`;

const spin = keyframes`
  from { transform: rotate(0deg); }
  to { opacity: 1; transform: translateY(0); }
`;

// --- [Styled Components - moved from App.js] ---

// KPI 그리드: 핵심 성과 지표(KPI) 카드들을 정렬하는 그리드 레이아웃입니다.
const KpiGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
  animation: ${css`${fadeIn} 0.5s ease forwards`};
`;

// KPI 카드: 개별 핵심 성과 지표를 표시하는 카드입니다.
const KpiCard = styled.div`
  background-color: ${props => props.theme.colors.surfaceTransparent};
  padding: 20px;
  border-radius: 20px;
  border: 1px solid ${props => props.theme.colors.border};
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
`;

// AI 배너: AI 인사이트 및 관련 액션을 표시하는 배너입니다.
const AiBanner = styled.div`
  background-color: rgba(37, 99, 235, 0.1);
  border: 1px solid rgba(37, 99, 235, 0.3);
  padding: 20px;
  border-radius: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  animation: ${css`${fadeIn} 0.5s ease forwards`};
  margin-top: 32px; /* Added margin-top for spacing */
`;

// AI 버튼: AI 인사이트 생성 기능을 트리거하는 버튼입니다.
const AiButton = styled.button`
  background-color: ${props => props.theme.colors.primaryDark};
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 12px;
  font-weight: 900;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  &:hover { background-color: ${props => props.theme.colors.primary}; }
  &:disabled { opacity: 0.5; }

  svg { animation: ${css`${spin} 1s linear infinite`};}
`;

// 리스트 뷰 전용 스타일
const StatusTable = styled.div` width: 100%; display: flex; flex-direction: column; gap: 12px; margin-top: 32px; `;
const ZoneRow = styled.div`
  display: grid; grid-template-columns: 0.8fr 1.5fr 1.5fr 1fr 1fr auto;
  gap: 16px;
  align-items: center; background: ${props => props.theme.colors.surface}; border: 1px solid ${props => props.theme.colors.border};
  border-radius: 16px; padding: 16px 24px; cursor: pointer;
  &:hover { border-color: ${props => props.theme.colors.primary}; }
`;
const LoadBar = styled.div`
  width: 100px; height: 6px; background: ${props => props.theme.colors.border}; border-radius: 3px;
  position: relative; overflow: hidden;
  &::after {
    content: ''; position: absolute; left: 0; top: 0; height: 100%;
    width: ${props => props.val}%; background: ${props => props.val > 80 ? props.theme.colors.status.danger : props.theme.colors.primary};
  }
`;

// 오른쪽 사이드바 스타일
const RightSidebar = styled.div`
  width: 320px;
  height: 100vh;
  background: ${props => props.theme.colors.surface};
  border-left: 1px solid ${props => props.theme.colors.border};
  padding: 24px;
  overflow-y: auto;
  flex-shrink: 0;
  animation: ${fadeIn} 0.3s ease-out;
  box-sizing: border-box;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: ${props => props.theme.colors.border};
    border-radius: 3px;
  }
`;

const SidebarTitle = styled.h3`
  font-size: 16px;
  font-weight: 900;
  color: ${props => props.theme.colors.text.main};
  margin: 0 0 24px 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ControlGroup = styled.div`
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid ${props => props.theme.colors.border};

  &:last-child {
    border-bottom: none;
  }
`;

const ControlLabel = styled.label`
  display: block;
  font-size: 12px;
  font-weight: 800;
  color: ${props => props.theme.colors.text.muted};
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
`;

const SliderInput = styled.input`
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: ${props => props.theme.colors.border};
  outline: none;
  -webkit-appearance: none;

  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: ${props => props.theme.colors.primary};
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
    transition: all 0.2s;

    &:hover {
      transform: scale(1.2);
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.6);
    }
  }

  &::-moz-range-thumb {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: ${props => props.theme.colors.primary};
    cursor: pointer;
    border: none;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
    transition: all 0.2s;

    &:hover {
      transform: scale(1.2);
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.6);
    }
  }
`;

const ValueDisplay = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 11px;
`;

const ValueNumber = styled.span`
  font-weight: 900;
  color: ${props => props.theme.colors.primary};
  font-size: 14px;
`;

const ResetButton = styled.button`
  width: 100%;
  padding: 12px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid ${props => props.theme.colors.primary};
  color: ${props => props.theme.colors.primary};
  border-radius: 12px;
  font-weight: 800;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    background: ${props => props.theme.colors.primary};
    color: white;
  }
`;



// 페이지 컨테이너
const PageContainer = styled.div`
  display: flex;
  flex-direction: row;
  gap: 0;
  height: 100%;
  animation: ${fadeIn} 0.5s ease forwards;
`;

// 메인 컨텐츠 래퍼
const MainContentWrapper = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 32px;
  overflow-y: auto;
  padding-right: 24px;
`;

const MacroDashboardPage = () => {
  const navigate = useNavigate();
  const [selectedZoneId, setSelectedZoneId] = useState(null);
  const [aiInsight, setAiInsight] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  
  // 시뮬레이션 파라미터
  const [simParams, setSimParams] = useState({
    throughputMultiplier: 1.0,  // 0.5 ~ 2.0
    speedMultiplier: 1.0,       // 0.5 ~ 2.0
    congestionLevel: 70,        // 0 ~ 100
    errorRate: 5                // 0 ~ 50
  });
  
  // 실제 데이터
  const [zonesSummary, setZonesSummary] = useState([]);
  const [bottlenecks, setBottlenecks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // KPI 데이터
  const [kpiMetrics, setKpiMetrics] = useState({
    totalThroughput: 0,
    avgSpeed: 0,
    bottleneckCount: 0,
    normalSensors: 0,
    totalSensors: 0
  });

  // 파라미터 변경 핸들러
  const handleParamChange = async (key, value) => {
    const newParams = {
      ...simParams,
      [key]: parseFloat(value)
    };
    setSimParams(newParams);
    
    // 센서 시뮬레이터에 실시간 반영
    try {
      await apiService.updateSimulationParams(newParams);
      console.log('시뮬레이션 파라미터 업데이트 성공:', newParams);
    } catch (err) {
      console.error('시뮬레이션 파라미터 업데이트 실패:', err);
    }
  };

  // 파라미터 초기화
  const resetParams = async () => {
    const defaultParams = {
      throughputMultiplier: 1.0,
      speedMultiplier: 1.0,
      congestionLevel: 70,
      errorRate: 5
    };
    setSimParams(defaultParams);
    
    try {
      await apiService.updateSimulationParams(defaultParams);
      console.log('시뮬레이션 파라미터 초기화 완료');
    } catch (err) {
      console.error('시뮬레이션 파라미터 초기화 실패:', err);
    }
  };

  // 실시간 데이터 가져오기
  const fetchData = useCallback(async () => {
    try {
      const [summaryData, bottleneckData] = await Promise.all([
        apiService.getZonesSummary(1),
        apiService.getBottlenecks(1)
      ]);
      
      setError(null);
      
      // 데이터가 실제로 변경되었는지 확인
      const summaryChanged = JSON.stringify(zonesSummary) !== JSON.stringify(summaryData);
      const bottleneckChanged = JSON.stringify(bottlenecks) !== JSON.stringify(bottleneckData);
      
      if (summaryChanged) {
        setZonesSummary(summaryData);
      }
      
      if (bottleneckChanged) {
        setBottlenecks(bottleneckData);
      }
      
      // KPI는 summary 데이터가 변경되었을 때만 재계산
      if (summaryChanged) {
        const totalThroughput = summaryData.reduce((sum, zone) => sum + zone.total_throughput, 0);
        const avgSpeed = summaryData.length > 0 
          ? summaryData.reduce((sum, zone) => sum + zone.avg_speed, 0) / summaryData.length 
          : 0;
        
        setKpiMetrics({
          totalThroughput,
          avgSpeed: avgSpeed.toFixed(2),
          bottleneckCount: bottleneckData.length,
          normalSensors: summaryData.reduce((sum, zone) => sum + zone.data_points, 0),
          totalSensors: summaryData.length
        });
      }
      
    } catch (err) {
      console.error('데이터 가져오기 실패:', err);
      setError('데이터를 불러올 수 없습니다. 백엔드 서버 상태를 확인하세요.');
    }
  }, [zonesSummary, bottlenecks]);

  // 초기 로드 및 5초마다 자동 새로고침
  useEffect(() => {
    // 처음 로드할 때만 loading true
    const loadInitial = async () => {
      setLoading(true);
      await fetchData();
      setLoading(false);
    };
    
    loadInitial();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // AI 인사이트를 생성하는 함수
  const generateAIInsight = () => {
    setIsGenerating(true);
    setTimeout(() => {
      const topBottleneck = bottlenecks[0];
      if (topBottleneck) {
        setAiInsight(`${topBottleneck.zone_id} 구역에서 병목 스코어 ${topBottleneck.bottleneck_score}로 감지됨. 우회 경로 확보를 권고합니다.`);
      } else {
        setAiInsight("모든 구역이 정상 운영 중입니다.");
      }
      setIsGenerating(false);
    }, 1500);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Loader2 size={40} style={{ animation: 'spin 1s linear infinite' }} />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <AlertTriangle size={40} color="#ef4444" />
        <p style={{ marginTop: '16px', color: '#ef4444' }}>{error}</p>
      </div>
    );
  }

  return (
    <PageContainer>
      {/* 메인 콘텐츠 영역 */}
      <MainContentWrapper>
        {/* KPI 지표 그리드 */}
        <KpiGrid>
        {[
          { label: '총 처리량 (1H)', value: kpiMetrics.totalThroughput.toLocaleString(), color: '#60a5fa', icon: <ShoppingCart size={16}/> },
          { label: '평균 속도', value: `${kpiMetrics.avgSpeed} m/s`, color: '#10b981', icon: <Activity size={16}/> },
          { label: '활성 병목', value: `${kpiMetrics.bottleneckCount}건`, color: '#f97316', icon: <Zap size={16}/> },
          { label: '정상 센서', value: `${kpiMetrics.normalSensors}/${kpiMetrics.totalSensors}`, color: '#10b981', icon: <Cpu size={16}/> },
        ].map((kpi, i) => (
          <KpiCard key={i}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '10px', fontWeight: 900, color: 'inherit' }}>{kpi.label}</span>
              <div style={{ padding: '6px', borderRadius: '8px', backgroundColor: 'rgba(0,0,0,0.1)', color: kpi.color }}>{kpi.icon}</div>
            </div>
            <p style={{ fontSize: '24px', fontWeight: 900, fontFamily: 'monospace', margin: 0 }}>{kpi.value}</p>
          </KpiCard>
        ))}
      </KpiGrid>

      {/* AI 배너 및 인사이트 */}
      <AiBanner>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ backgroundColor: '#2563eb', padding: '10px', borderRadius: '16px' }}><BrainCircuit color="white" size={24} /></div>
          <div>
            <h4 style={{ fontSize: '9px', fontWeight: 900, color: '#60a5fa', margin: 0 }}>AI OPERATIONS ADVISOR</h4>
            <p style={{ fontSize: '13px', color: 'inherit', fontWeight: 'bold', margin: '4px 0 0' }}>{aiInsight || "운영 전략 실시간 분석 대기 중..."}</p>
          </div>
        </div>
        <AiButton onClick={generateAIInsight} disabled={isGenerating}>
          {isGenerating ? <Loader2 size={14}/> : 'ANALYZE'}
        </AiButton>
      </AiBanner>

      {/* Zone 상태 테이블 */}
      <StatusTable>
        {zonesSummary.map(zone => {
          const status = zone.bottleneck_count > 3 ? 'critical' : zone.avg_speed < 1.5 ? 'warning' : 'normal';
          const loadPercent = Math.min(100, (zone.total_throughput / 100) * 100);
          
          return (
            <ZoneRow 
              key={zone.zone_id} 
              onClick={() => navigate('/zone_analytics', { 
                state: { 
                  zoneId: zone.zone_id, 
                  zoneName: zone.zone_id,
                  sensorCount: ZONE_SENSOR_CONFIG[zone.zone_id] || 100
                } 
              })}
            >
              <span style={{ color: 'inherit', fontWeight: 900 }}>{zone.zone_id}</span>
              <span style={{ fontWeight: 800 }}>처리량: {zone.total_throughput}</span>
              <div>
                <div style={{ fontSize: '12px', marginBottom: '4px' }}>평균 {zone.avg_speed} m/s</div>
                <LoadBar val={loadPercent} />
              </div>
              <span style={{ fontWeight: 900 }}>데이터: {zone.data_points}건</span>
              <span style={{ 
                color: status === 'critical' ? '#ef4444' : status === 'warning' ? '#f59e0b' : '#10b981', 
                fontSize: '10px', 
                fontWeight: 900 
              }}>
                {status.toUpperCase()}
              </span>
              <ChevronRight size={18} color="#475569" />
            </ZoneRow>
          );
        })}
      </StatusTable>

      {/* 병목 현황 */}
      {bottlenecks.length > 0 && (
        <div style={{ marginTop: '32px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 900, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={20} color="#ef4444" />
            활성 병목 현황
          </h3>
          <div style={{ display: 'grid', gap: '12px' }}>
            {bottlenecks.slice(0, 5).map((bottleneck, idx) => (
              <div 
                key={idx}
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  padding: '16px',
                  borderRadius: '12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <span style={{ fontWeight: 900, fontSize: '14px' }}>{bottleneck.aggregated_id}</span>
                  <span style={{ marginLeft: '12px', color: '#666', fontSize: '12px' }}>
                    Zone: {bottleneck.zone_id}
                  </span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '20px', fontWeight: 900, color: '#ef4444' }}>
                    {(bottleneck.bottleneck_score * 100).toFixed(0)}%
                  </div>
                  <div style={{ fontSize: '10px', color: '#666' }}>병목 스코어</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      </MainContentWrapper>

      {/* 오른쪽 사이드바 - 시뮬레이션 파라미터 제어 */}
      <RightSidebar>
        <SidebarTitle>
          <Zap size={18} />
          시뮬레이션 제어
        </SidebarTitle>

        <ControlGroup>
          <ControlLabel>처리량 증감율</ControlLabel>
          <SliderInput
            type="range"
            min="0.5"
            max="2"
            step="0.1"
            value={simParams.throughputMultiplier}
            onChange={(e) => handleParamChange('throughputMultiplier', e.target.value)}
          />
          <ValueDisplay>
            <span>낮음</span>
            <ValueNumber>{(simParams.throughputMultiplier * 100).toFixed(0)}%</ValueNumber>
            <span>높음</span>
          </ValueDisplay>
        </ControlGroup>

        <ControlGroup>
          <ControlLabel>속도 증감율</ControlLabel>
          <SliderInput
            type="range"
            min="0.5"
            max="2"
            step="0.1"
            value={simParams.speedMultiplier}
            onChange={(e) => handleParamChange('speedMultiplier', e.target.value)}
          />
          <ValueDisplay>
            <span>느림</span>
            <ValueNumber>{(simParams.speedMultiplier * 100).toFixed(0)}%</ValueNumber>
            <span>빠름</span>
          </ValueDisplay>
        </ControlGroup>

        <ControlGroup>
          <ControlLabel>혼잡도 레벨</ControlLabel>
          <SliderInput
            type="range"
            min="0"
            max="100"
            step="5"
            value={simParams.congestionLevel}
            onChange={(e) => handleParamChange('congestionLevel', e.target.value)}
          />
          <ValueDisplay>
            <span>여유</span>
            <ValueNumber>{simParams.congestionLevel}%</ValueNumber>
            <span>포화</span>
          </ValueDisplay>
        </ControlGroup>

        <ControlGroup>
          <ControlLabel>에러율</ControlLabel>
          <SliderInput
            type="range"
            min="0"
            max="50"
            step="2"
            value={simParams.errorRate}
            onChange={(e) => handleParamChange('errorRate', e.target.value)}
          />
          <ValueDisplay>
            <span>정상</span>
            <ValueNumber>{simParams.errorRate}%</ValueNumber>
            <span>이상</span>
          </ValueDisplay>
        </ControlGroup>

        <ResetButton onClick={resetParams}>
          초기값으로 복원
        </ResetButton>

        <div style={{ marginTop: '32px', padding: '16px', background: 'rgba(59, 130, 246, 0.05)', borderRadius: '12px', fontSize: '11px', color: '#9ca3af', lineHeight: '1.6' }}>
          💡 <strong>팁:</strong> 슬라이더를 조정하여 시뮬레이션 파라미터를 실시간으로 변경할 수 있습니다. 각 요인이 시스템에 미치는 영향을 관찰하세요.
        </div>
      </RightSidebar>
    </PageContainer>
  );
};

export default MacroDashboardPage;