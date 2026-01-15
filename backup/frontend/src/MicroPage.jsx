import React, { useState, useEffect } from 'react';
import styled, { keyframes } from 'styled-components';
import { 
  BarChart3, Activity, Repeat, Zap, Cpu, Clock, 
  ChevronRight, Circle, LayoutDashboard 
} from 'lucide-react';

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
  color: #e2e8f0;
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
    color: #ffffff;
    span { color: #3b82f6; }
  }
  p {
    font-size: 12px;
    font-weight: 700;
    color: #64748b;
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
  h4 { color: #ef4444; font-size: 10px; font-weight: 900; margin: 0 0 8px; }
  p { color: #ef4444; font-size: 28px; font-weight: 900; margin: 0; font-family: 'monospace'; }
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
`;

const MetricCard = styled.div`
  background: #0b0e14;
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 24px;
  position: relative;
  transition: border-color 0.3s;
  &:hover { border-color: #3b82f6; }
`;

const MetricHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  span { font-size: 11px; font-weight: 800; color: #64748b; }
  svg { color: ${props => props.color || '#3b82f6'}; opacity: 0.8; }
`;

const MetricValue = styled.div`
  h3 { font-size: 24px; font-weight: 900; margin: 0; color: #ffffff; }
  p { font-size: 10px; color: #475569; margin-top: 4px; font-weight: 700; }
`;

const VisualizationRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  height: 400px;
`;

const ChartContainer = styled.div`
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid #1e293b;
  border-radius: 24px;
  padding: 24px;
  display: flex;
  flex-direction: column;
`;

const ChartTitle = styled.div`
  font-size: 11px;
  font-weight: 900;
  color: #64748b;
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

const SensorRow = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  span { font-size: 12px; font-weight: 900; color: #475569; width: 24px; }
`;

const GridBox = styled.div`
  flex: 1;
  height: 32px;
  background: ${props => props.active ? 'rgba(59, 130, 246, 0.5)' : '#1e293b'};
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.05);
`;

// --- [Main Component] ---
const MicroPage = () => { // Renamed from LogisticsZoneAnalytics
  const [metrics, setMetrics] = useState({
    tph: 3922, congestion: 78, recirculation: 12.5, efficiency: 91.3, oee: 72.8, bottleneck: 498
  });

  return (
    <PageContainer>
      {/* 1. Header Section */}
      <TopHeader>
        <TitleSection>
          <h2>Logistics Zone <span>ANALYTICS</span></h2>
          <p>PK-01 | OPERATIONAL COST FOCUS</p>
        </TitleSection>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#0f172a', padding: '8px 16px', borderRadius: '20px', border: '1px solid #1e293b' }}>
            <Circle size={8} fill="#10b981" color="#10b981" />
            <span style={{ fontSize: '10px', fontWeight: 900, color: '#94a3b8' }}>LIVE: ANALYTICS ACTIVE</span>
          </div>
          <LossCard>
            <h4>TARGET ZONE LOSS ESTIMATE</h4>
            <p>₩29,070</p>
          </LossCard>
        </div>
      </TopHeader>

      {/* 2. KPI Metrics Grid */}
      <MetricsGrid>
        <MetricCard>
          <MetricHeader><span style={{ color: '#ffffff' }}>TPH (Throughput)</span><BarChart3 size={18} /></MetricHeader>
          <MetricValue>
            <h3>{metrics.tph}</h3>
            <p>Units/hr</p>
          </MetricValue>
        </MetricCard>
        <MetricCard>
          <MetricHeader><span style={{ color: '#ffffff' }}>Congestion Index</span><Activity size={18} color="#fbbf24" /></MetricHeader>
          <MetricValue>
            <h3>{metrics.congestion}%</h3>
            <p>Density</p>
          </MetricValue>
        </MetricCard>
        <MetricCard>
          <MetricHeader><span style={{ color: '#ffffff' }}>Recirculation</span><Repeat size={18} color="#10b981" /></MetricHeader>
          <MetricValue>
            <h3>{metrics.recirculation}%</h3>
            <p>Loop Rate</p>
          </MetricValue>
        </MetricCard>
        <MetricCard>
          <MetricHeader><span style={{ color: '#ffffff' }}>Energy Efficiency</span><Zap size={18} /></MetricHeader>
          <MetricValue>
            <h3>{metrics.efficiency}%</h3>
            <p>kW/Load</p>
          </MetricValue>
        </MetricCard>
        <MetricCard>
          <MetricHeader><span style={{ color: '#ffffff' }}>OEE Status</span><Cpu size={18} color="#10b981" /></MetricHeader>
          <MetricValue>
            <h3>{metrics.oee}%</h3>
            <p>Health</p>
          </MetricValue>
        </MetricCard>
      </MetricsGrid>

      {/* 3. Visualizations */}
      <VisualizationRow>
        {/* Trend Chart (Placeholder style as per image) */}
        <ChartContainer>
          <ChartTitle><Activity size={14} /> LOAD TELEMETRY TREND (REAL-TIME)</ChartTitle>
          <div style={{ flex: 1, background: 'linear-gradient(transparent, rgba(59, 130, 246, 0.1))', borderBottom: '2px solid #3b82f6', position: 'relative', overflow: 'hidden' }}>
             {/* Simple SVG Wave to mimic chart in image */}
             <svg width="100%" height="100%" viewBox="0 0 400 150" preserveAspectRatio="none">
               <path d="M0,100 Q50,80 100,110 T200,90 T300,120 T400,80 L400,150 L0,150 Z" fill="rgba(59, 130, 246, 0.2)" stroke="#3b82f6" strokeWidth="2" />
             </svg>
          </div>
        </ChartContainer>

        {/* Sensor Grid Flow */}
        <ChartContainer>
          <ChartTitle><LayoutDashboard size={14} /> RAIL SENSOR GRID FLOW (3 Lines)</ChartTitle>
          <SensorGrid>
            {['L1', 'L2', 'L3'].map((line) => (
              <SensorRow key={line}>
                <span>{line}</span>
                {Array.from({ length: 15 }).map((_, i) => (
                  <GridBox key={i} active={Math.random() > 0.7} />
                ))}
              </SensorRow>
            ))}
          </SensorGrid>
        </ChartContainer>
      </VisualizationRow>
    </PageContainer>
  );
};

export default MicroPage;