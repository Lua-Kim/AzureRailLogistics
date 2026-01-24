import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Activity, Database, Server, RefreshCw } from 'lucide-react';

const Container = styled.div`
  padding: 24px;
  color: ${props => props.theme.colors.text.main};
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const Title = styled.h2`
  font-size: 24px;
  font-weight: 900;
  display: flex;
  align-items: center;
  gap: 12px;
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

  const fetchData = async () => {
    try {
      const [statusRes, basketsRes, movementsRes] = await Promise.all([
        fetch('http://localhost:8000/simulator/status'),
        fetch('http://localhost:8000/baskets'),
        fetch('http://localhost:8000/baskets/movements')
      ]);
      
      setStatus(await statusRes.json());
      setBaskets(await basketsRes.json());
      setMovements(await movementsRes.json());
    } catch (err) {
      console.error("Debug fetch error:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

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
          <LogContainer>{JSON.stringify(baskets, null, 2)}</LogContainer>
        </Card>
        
        <Card style={{ gridColumn: '1 / -1' }}>
          <CardHeader><RefreshCw size={20}/> Movement Logs (Real-time)</CardHeader>
          <LogContainer>
            {movements.length === 0 ? 'No movements detected.' : 
              movements.map((m, i) => (
                <div key={i} style={{ marginBottom: '4px', borderBottom: '1px solid #33333340', paddingBottom: '4px' }}>
                  [{m.timestamp}] <strong>{m.basket_id}</strong> @ {m.zone_id}-{m.line_id} 
                  ({m.position_meters.toFixed(2)}m / {m.line_length}m) - {m.progress_percent.toFixed(1)}%
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