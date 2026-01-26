import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Activity, Database, Server, RefreshCw, Radio } from 'lucide-react';
import axios from 'axios';

const Container = styled.div`
  padding: 24px;
  color: ${props => props.theme.colors.text.main};
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow: hidden;
`;

const Title = styled.h2`
  font-size: 24px;
  font-weight: 900;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  flex: 1;
  min-height: 0;
`;

const Card = styled.div`
  background-color: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const CardHeader = styled.h3`
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: ${props => props.theme.colors.primary};
`;

const LogContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  background-color: ${props => props.theme.colors.background};
  padding: 12px;
  border-radius: 8px;
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
  border: 1px solid ${props => props.theme.colors.border};
  color: ${props => props.theme.colors.text.sub};
`;

const VisualizationDebugPage = () => {
  const [status, setStatus] = useState(null);
  const [baskets, setBaskets] = useState(null);
  const [movements, setMovements] = useState([]);
  const [events, setEvents] = useState([]);
  const [showActiveSensors, setShowActiveSensors] = useState(false);

  const fetchData = async () => {
    try {
      const [statusRes, basketsRes, movementsRes, eventsRes] = await Promise.all([
        fetch('http://localhost:8000/simulator/status'),
        fetch('http://localhost:8000/baskets'),
        fetch('http://localhost:8000/baskets/movements'),
        fetch(`http://localhost:8000/events/latest?count=20&only_active=${showActiveSensors}`)
      ]);
      
      if (statusRes.ok) setStatus(await statusRes.json());
      if (basketsRes.ok) setBaskets(await basketsRes.json());
      if (movementsRes.ok) {
        const moveData = await movementsRes.json();
        setMovements(Array.isArray(moveData) ? moveData : []);
      }
      if (eventsRes.ok) {
        const eventsData = await eventsRes.json();
        setEvents(eventsData.events || []);
      }
    } catch (err) {
      console.error("Debug fetch error:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, [showActiveSensors]);

  // [핵심] 별도 API 대신 baskets 데이터에서 직접 이동 중인 바스켓 추출
  const activeMovements = baskets?.baskets?.filter(b => b.status === 'in_transit' || b.status === 'moving') || [];

  return (
    <Container>
      <Title><Activity /> System Debug</Title>
      
      <Grid>
        <Card>
          <CardHeader><Server size={20}/> Simulator Status</CardHeader>
          <LogContainer>{JSON.stringify(status, null, 2)}</LogContainer>
        </Card>
        
        <Card>
          <CardHeader><Database size={20}/> Basket Info</CardHeader>
          <LogContainer>
            {baskets ? (
              <>
                <div style={{ marginBottom: '10px', paddingBottom: '10px', borderBottom: '1px solid #333' }}>
                  <strong>Statistics:</strong> Total: {baskets.statistics?.total}, In Transit: {baskets.statistics?.in_transit}, Arrived: {baskets.statistics?.arrived}
                </div>
                <div><strong>Active Baskets List:</strong></div>
                {activeMovements.length > 0 ? (
                  activeMovements.map(b => (
                      <div key={b.basket_id} style={{ fontSize: '11px', marginTop: '4px' }}>
                        <span style={{ color: '#3b82f6', fontWeight: 'bold' }}>{b.basket_id}</span> : {b.zone_id} / {b.line_id} ({b.status})
                      </div>
                    ))
                ) : (
                  <div style={{ color: '#888', marginTop: '4px' }}>No active baskets.</div>
                )}
              </>
            ) : 'Loading...'}
          </LogContainer>
        </Card>
        
        <Card style={{ gridColumn: '1 / -1' }}>
          <CardHeader><RefreshCw size={20}/> Movement Logs (Real-time)</CardHeader>
          <LogContainer>
            {activeMovements.length === 0 ? (
               <div style={{ padding: '20px', textAlign: 'center', color: '#888' }}>
                현재 이동 중인 바스켓이 없습니다.<br/>좌측 메뉴의 <strong>'바스켓 시각화'</strong> 페이지에서 바스켓을 투입해주세요.
              </div>
            ) : 
              activeMovements.map((b, i) => (
                <div key={b.basket_id} style={{ marginBottom: '4px', borderBottom: '1px solid #33333340', paddingBottom: '4px' }}>
                  [{new Date().toLocaleTimeString()}] <strong>{b.basket_id}</strong> @ {b.zone_id}-{b.line_id} 
                  ({Number(b.position_meters || 0).toFixed(2)}m / {b.line_length}m) - {Number(b.progress_percent || 0).toFixed(1)}%
                </div>
              ))
            }
          </LogContainer>
        </Card>

        <Card style={{ gridColumn: '1 / -1' }}>
          <CardHeader>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Radio size={20}/> Real-time Sensor Events (Kafka)
            </div>
            <label style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontWeight: 'normal' }}>
              <input 
                type="checkbox" 
                checked={showActiveSensors} 
                onChange={(e) => setShowActiveSensors(e.target.checked)} 
              /> 감지 신호만 보기 (ON)
            </label>
          </CardHeader>
          <LogContainer>
            {(!events || events.length === 0) ? 'No sensor events detected.' : 
              events.slice().reverse().map((e, i) => (
                <div key={i} style={{ marginBottom: '4px', borderBottom: '1px solid #33333340', paddingBottom: '4px' }}>
                  <span style={{color: '#888'}}>[{e.timestamp}]</span>{' '}
                  <strong style={{color: '#3b82f6'}}>{e.sensor_id}</strong>{' '}
                  <span>({e.zone_id})</span>{' '}
                  Signal: <span style={{
                    color: e.signal ? '#10b981' : '#ef4444', 
                    fontWeight: 'bold'
                  }}>{e.signal ? 'ON' : 'OFF'}</span>
                </div>
              ))
            }
          </LogContainer>
        </Card>
      </Grid>
    </Container>
  );
};

export default VisualizationDebugPage;
