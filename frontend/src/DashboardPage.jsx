import React, { useState, useEffect } from 'react';
import styled, { keyframes, css } from 'styled-components';
import { useNavigate } from 'react-router-dom';
import { 
  ShoppingCart, RotateCcw, Truck, TrendingDown, Thermometer, Wind, Users, Cpu, ChevronRight,
  BarChart3, Zap, Circle, BrainCircuit, Loader2, Play, Pause // Added new icons
} from 'lucide-react';

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
  display: grid; grid-template-columns: 0.8fr 1.5fr 1.5fr 1fr 1fr 0.5fr;
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

// 재생바: 시뮬레이션 또는 데이터 이력 재생을 위한 컨트롤 바입니다.
const PlaybackBar = styled.div`
  background-color: ${props => props.theme.colors.surfaceTransparent};
  padding: 20px;
  border-radius: 16px;
  border: 1px solid ${props => props.theme.colors.border};
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 32px;
`;

// 슬라이더: 재생바 내에서 시간 또는 데이터 포인트를 조절하는 데 사용됩니다.
const Slider = styled.input.attrs({ type: 'range' })`
  flex: 1;
  height: 4px;
  background: ${props => props.theme.colors.text.muted};
  border-radius: 2px;
  appearance: none;
  cursor: pointer;

  &::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: ${props => props.theme.colors.primary};
  }
`;

const MacroDashboardPage = () => {
  const navigate = useNavigate();
    // 선택된 구역의 ID를 관리하는 상태
  const [selectedZoneId, setSelectedZoneId] = useState('PK-01');
  // AI 인사이트 텍스트를 관리하는 상태
  const [aiInsight, setAiInsight] = useState("");
  // AI 인사이트 생성 중인지 여부를 나타내는 상태
  const [isGenerating, setIsGenerating] = useState(false);
  // 재생 모드 활성화 여부를 관리하는 상태
  const [isPlaybackMode, setIsPlaybackMode] = useState(false);
  // 재생 인덱스를 관리하는 상태 (데이터 이력 탐색용)
  const [playbackIndex, setPlaybackIndex] = useState(0);

    // 대시보드 구성을 위한 데이터 (구역, 연결 등)
  const [config, setConfig] = useState({
    centerName: "Incheon Global Hub-01",
    width: 1200, height: 800,
    zones: [
      { id: 'IN-01', name: 'Inbound Dock', x: 150, y: 400, type: 'entry', lines: 2, length: 15, workers: 4, status: 'normal', load: 45, temp: 32, vib: 1.2 },
      { id: 'SR-01', name: 'Sorter Alpha', x: 450, y: 400, type: 'process', lines: 4, length: 30, workers: 2, status: 'warning', load: 72, temp: 48, vib: 3.8 },
      { id: 'BF-01', name: 'Storage Buffer', x: 450, y: 150, type: 'buffer', lines: 1, length: 50, workers: 1, status: 'normal', load: 20, temp: 28, vib: 0.5 },
      { id: 'PK-01', name: 'Picking Zone', x: 800, y: 400, type: 'process', lines: 3, length: 20, workers: 8, status: 'critical', load: 92, temp: 55, vib: 5.2 },
      { id: 'OT-01', name: 'Outbound', x: 1050, y: 400, type: 'exit', lines: 2, length: 15, workers: 3, status: 'normal', load: 55, temp: 35, vib: 1.5 },
    ],
    connections: [
      { from: 'IN-01', to: 'SR-01' }, { from: 'SR-01', to: 'BF-01' },
      { from: 'SR-01', to: 'PK-01' }, { from: 'PK-01', to: 'OT-01' },
    ]
  });

  // 데이터 변경 이력을 저장하는 상태 (재생 기능용)
  const [history, setHistory] = useState([]); 
  // 핵심 성과 지표(KPI) 데이터를 관리하는 상태
  const [kpiMetrics, setKpiMetrics] = useState({
    orders: 12450,
    returns: 840,
    unloading: 5200,
    loss: 7.53,
    bottleneckCount: 28,
    bottleneckWaitTime: 4.2,
    bottleneckLoss: 1.2
  });

  // 현재 표시할 데이터 (재생 모드 여부에 따라 config 또는 history에서 가져옴)
  const currentData = isPlaybackMode ? history[playbackIndex] || config : config;
  // 현재 선택된 구역의 데이터를 찾습니다.
  const selectedZone = currentData.zones.find(z => z.id === selectedZoneId) || currentData.zones[0];

  // 데이터 자동 업데이트 및 이력 저장 로직 (3초마다 실행)
  useEffect(() => {
    if (isPlaybackMode) return; // 재생 모드일 때는 업데이트하지 않음
    const interval = setInterval(() => {
      setConfig(prev => {
        const nextZones = prev.zones.map(z => {
          const drift = (Math.random() - 0.5) * 6; // 데이터에 약간의 무작위 변동 추가
          const nextLoad = Math.max(10, Math.min(100, z.load + drift)); // 부하량 업데이트
          return {
            ...z, load: nextLoad, temp: 30 + (nextLoad / 2.5), vib: (nextLoad / 20) + Math.random(),
            status: nextLoad > 88 ? 'critical' : nextLoad > 70 ? 'warning' : 'normal' // 상태 업데이트
          };
        });
        const newState = { ...prev, zones: nextZones, timestamp: new Date().toLocaleTimeString() };
        setHistory(h => [newState, ...h].slice(0, 40)); // 이력에 최신 상태 추가 (최대 40개 유지)
        return newState;
      });
    }, 3000); // 3초마다 실행

    // 컴포넌트 언마운트 시 인터벌 정리
    return () => clearInterval(interval);
  }, [isPlaybackMode]); // isPlaybackMode가 변경될 때만 재실행

  // AI 인사이트를 생성하는 함수
  const generateAIInsight = () => {
    setIsGenerating(true); // AI 생성 중 상태로 설정
    setTimeout(() => {
      // 1.5초 후 인사이트 메시지 설정 (임시 로직)
      setAiInsight(`${selectedZone.name}의 가동률이 ${selectedZone.load.toFixed(1)}%로 높습니다. 우회 경로 확보를 권고합니다.`);
      setIsGenerating(false); // AI 생성 완료 상태로 설정
    }, 1500);
  };

    return (
        <>
            {/* KPI 지표 그리드 */}
            <KpiGrid>
              {[
                { label: 'Today Orders', value: kpiMetrics.orders.toLocaleString(), color: '#60a5fa', icon: <ShoppingCart size={16}/> },
                { label: 'Returns', value: kpiMetrics.returns.toLocaleString(), color: '#fbbf24', icon: <RotateCcw size={16}/> },
                { label: 'Unloading', value: kpiMetrics.unloading.toLocaleString(), color: '#10b981', icon: <Truck size={16}/> },
                { label: 'Loss Estimate', value: `₩${kpiMetrics.loss}M`, color: '#ef4444', icon: <TrendingDown size={16}/> },
                { label: '병목 발생', value: `${kpiMetrics.bottleneckCount}건`, color: '#f97316', icon: <Zap size={16}/> },
                { label: '병목 대기시간', value: `${kpiMetrics.bottleneckWaitTime}H`, color: '#f59e0b', icon: <Loader2 size={16}/> },
                { label: '병목 손실액', value: `₩${kpiMetrics.bottleneckLoss}M`, color: '#ef4444', icon: <TrendingDown size={16}/> },
              ].map((kpi, i) => (
                <KpiCard key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontSize: '10px', fontWeight: 900, color: 'inherit' }}>{kpi.label}</span>
                    <div style={{ padding: '6px', borderRadius: '8px', backgroundColor: 'rgba(0,0,0,0.1)', color: kpi.color }}>{kpi.icon}</div>
                  </div>
                  <p style={{ fontSize: '24px', fontWeight: 900, fontFamily: 'monospace', margin: 0, color: 'inherit' }}>{kpi.value}</p>
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

            <StatusTable>
            {currentData.zones.map(zone => (
              <ZoneRow key={zone.id} onClick={() => { setSelectedZoneId(zone.id); navigate('/zone_analytics', { state: { zoneId: zone.id, zoneName: zone.name } }); }}>
                <span style={{ color: 'inherit', fontWeight: 900 }}>{zone.id}</span>
                <span style={{ fontWeight: 800 }}>{zone.name}</span>
                <div>
                  <div style={{ fontSize: '12px', marginBottom: '4px' }}>{zone.load}%</div>
                  <LoadBar val={zone.load} />
                </div>
                <span style={{ fontWeight: 900, color: zone.temp > 60 ? 'red' : 'inherit' }}>{zone.temp}°C</span>
                <span style={{ color: zone.status === 'warning' ? '#f59e0b' : '#10b981', fontSize: '10px' }}>{zone.status.toUpperCase()}</span>
                <ChevronRight size={18} color="#475569" />
              </ZoneRow>
            ))}
          </StatusTable>

            {/* 데이터 재생 컨트롤 바 */}
            <PlaybackBar>
              <button onClick={() => setIsPlaybackMode(!isPlaybackMode)} style={{ background: isPlaybackMode ? '#f59e0b' : 'grey', border: 'none', padding: '14px', borderRadius: '12px', color: 'white', cursor: 'pointer' }}>
                {isPlaybackMode ? <Pause size={20}/> : <Play size={20}/>}
              </button>
              <Slider min="0" max={Math.max(0, history.length - 1)} value={playbackIndex} onChange={(e) => { setPlaybackIndex(parseInt(e.target.value)); setIsPlaybackMode(true); }} />
            </PlaybackBar>
        </>
    );
};

export default MacroDashboardPage;