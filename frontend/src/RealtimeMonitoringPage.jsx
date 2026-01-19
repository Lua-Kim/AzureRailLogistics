import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Activity, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import axios from 'axios';

const PageContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 20px;
  background-color: ${props => props.theme.colors.background};
  min-height: 100vh;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background-color: ${props => props.theme.colors.surface};
  border-radius: 12px;
  border: 1px solid ${props => props.theme.colors.border};
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
`;

const Title = styled.h1`
  font-size: 24px;
  font-weight: 900;
  color: ${props => props.theme.colors.text.main};
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;

  svg {
    color: ${props => props.theme.colors.primary};
  }
`;

const StatusBadge = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: ${props => props.isActive ? '#10b98166' : '#ef444466'};
  border: 1px solid ${props => props.isActive ? '#10b981' : '#ef4444'};
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  color: ${props => props.isActive ? '#10b981' : '#ef4444'};

  &::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: currentColor;
    box-shadow: 0 0 8px currentColor;
  }
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
`;

const Card = styled.div`
  background-color: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;

  &:hover {
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15);
  }
`;

const CardTitle = styled.h3`
  font-size: 12px;
  font-weight: 700;
  color: ${props => props.theme.colors.text.muted};
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 12px 0;
`;

const CardValue = styled.div`
  font-size: 32px;
  font-weight: 900;
  color: ${props => props.theme.colors.text.main};
  margin-bottom: 8px;
`;

const CardSubtext = styled.p`
  font-size: 12px;
  color: ${props => props.theme.colors.text.muted};
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
`;

const Table = styled.div`
  background-color: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
`;

const TableHeader = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
  gap: 16px;
  padding: 16px 20px;
  background-color: ${props => props.theme.colors.surfaceHighlight};
  border-bottom: 2px solid ${props => props.theme.colors.border};
  font-weight: 700;
  font-size: 12px;
  color: ${props => props.theme.colors.text.muted};
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const TableRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid ${props => props.theme.colors.border};
  align-items: center;
  transition: all 0.2s ease;

  &:hover {
    background-color: ${props => props.theme.colors.surfaceHighlight};
  }

  &:last-child {
    border-bottom: none;
  }
`;

const SensorValue = styled.span`
  font-size: 13px;
  font-weight: 600;
  color: ${props => props.theme.colors.text.main};
`;

const SignalBadge = styled.span`
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  background-color: ${props => props.signal ? '#10b98166' : '#ef444466'};
  color: ${props => props.signal ? '#10b981' : '#ef4444'};
`;

const BasketBadge = styled.span`
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  background-color: #3b82f666;
  color: #3b82f6;
`;

const ZoneBadge = styled.span`
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  background-color: #8b5cf666;
  color: #8b5cf6;
`;

const ChartContainer = styled.div`
  background-color: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
`;

const ChartTitle = styled.h3`
  font-size: 14px;
  font-weight: 700;
  color: ${props => props.theme.colors.text.main};
  margin: 0 0 20px 0;
`;

const BarChart = styled.div`
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 150px;
  gap: 8px;
`;

const Bar = styled.div`
  flex: 1;
  background: linear-gradient(to top, #3b82f6, #60a5fa);
  border-radius: 4px 4px 0 0;
  height: ${props => `${props.height}%`};
  position: relative;
  transition: all 0.3s ease;
  cursor: pointer;

  &:hover {
    filter: brightness(1.1);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  }

  &::after {
    content: '${props => props.value}';
    position: absolute;
    top: -20px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 12px;
    font-weight: 700;
    color: ${props => props.theme.colors.text.muted};
  }
`;

const RealtimeMonitoringPage = () => {
  const [stats, setStats] = useState({
    totalBaskets: 0,
    movingBaskets: 0,
    totalSensors: 0,
    activeSignals: 0,
    zones: [],
    recentEvents: [],
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [simulatorActive, setSimulatorActive] = useState(false);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const [basketsRes, eventsRes, zonesRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/baskets`),
          axios.get(`${API_BASE_URL}/events/latest?count=20`),
          axios.get(`${API_BASE_URL}/zones`),
        ]);

        // 바스켓 데이터 처리
        const basketData = basketsRes.data;
        const baskets = basketData.baskets || (Array.isArray(basketData) ? basketData : []);
        const movingBaskets = baskets.filter(b => b.status === 'moving' || b.status === 'in_transit').length;
        
        // 이벤트 데이터 처리
        const eventsData = eventsRes.data;
        const events = eventsData.events || (Array.isArray(eventsData) ? eventsData : []);
        const activeSignals = events.filter(e => e.signal === true).length;
        
        // 존 데이터 처리
        const zones = zonesRes.data || (Array.isArray(zonesRes.data) ? zonesRes.data : []);
        const totalSensors = zones.reduce((sum, zone) => sum + (zone.sensors || 0), 0);

        setStats({
          totalBaskets: baskets.length,
          movingBaskets: movingBaskets,
          totalSensors: totalSensors,
          activeSignals: activeSignals,
          zones: zones,
          recentEvents: events,
        });

        setLastUpdate(new Date());
        setError(null);
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000); // 3초마다 갱신

    return () => clearInterval(interval);
  }, []);

  const zoneStats = stats.zones.map((zone, idx) => ({
    name: zone.zone_id || `Zone ${idx + 1}`,
    sensors: zone.sensors || 0,
    lines: zone.lines || 0,
  }));

  const handleSimulatorToggle = async () => {
    try {
      const endpoint = simulatorActive ? '/simulator/stop' : '/simulator/start';
      await axios.post(`${API_BASE_URL}${endpoint}`);
      setSimulatorActive(!simulatorActive);
    } catch (err) {
      console.error('시뮬레이터 제어 실패:', err);
    }
  };

  return (
    <PageContainer>
      <Header>
        <Title>
          <Activity size={28} />
          실시간 모니터링
        </Title>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            onClick={handleSimulatorToggle}
            style={{
              padding: '8px 16px',
              backgroundColor: simulatorActive ? '#ef4444' : '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 700,
              transition: 'all 0.3s ease',
            }}
          >
            {simulatorActive ? '시뮬레이터 중지' : '시뮬레이터 시작'}
          </button>
          <StatusBadge isActive={simulatorActive}>
            {simulatorActive ? '라이브 스트리밍' : '대기 중'}
          </StatusBadge>
        </div>
      </Header>

      {error && (
        <Card style={{ backgroundColor: '#ef444420', borderColor: '#ef4444' }}>
          <CardTitle>오류</CardTitle>
          <CardValue style={{ color: '#ef4444', fontSize: '14px' }}>
            {error}
          </CardValue>
        </Card>
      )}

      <Grid>
        <Card>
          <CardTitle>총 바스켓</CardTitle>
          <CardValue>{stats.totalBaskets}</CardValue>
          <CardSubtext>
            <TrendingUp size={14} />
            {stats.movingBaskets}개 이동 중
          </CardSubtext>
        </Card>

        <Card>
          <CardTitle>활성 센서</CardTitle>
          <CardValue>{stats.activeSignals}</CardValue>
          <CardSubtext>
            <CheckCircle size={14} />
            총 {stats.totalSensors}개 센서
          </CardSubtext>
        </Card>

        <Card>
          <CardTitle>존 구역</CardTitle>
          <CardValue>{stats.zones.length}</CardValue>
          <CardSubtext>
            운영 중인 물류센터 구역
          </CardSubtext>
        </Card>

        <Card>
          <CardTitle>신호 감지율</CardTitle>
          <CardValue>
            {stats.totalSensors > 0 ? Math.round((stats.activeSignals / stats.totalSensors) * 100) : 0}%
          </CardValue>
          <CardSubtext>
            마지막 업데이트: {lastUpdate.toLocaleTimeString()}
          </CardSubtext>
        </Card>
      </Grid>

      {zoneStats.length > 0 && (
        <ChartContainer>
          <ChartTitle>존별 센서 분포</ChartTitle>
          <BarChart>
            {zoneStats.map((zone, idx) => (
              <Bar 
                key={idx} 
                height={(zone.sensors / Math.max(...zoneStats.map(z => z.sensors))) * 100}
                value={zone.sensors}
              />
            ))}
          </BarChart>
          <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '30px', fontSize: '12px' }}>
            {zoneStats.map((zone, idx) => (
              <div key={idx} style={{ textAlign: 'center', color: '#888' }}>
                {zone.name}
              </div>
            ))}
          </div>
        </ChartContainer>
      )}

      <Table>
        <TableHeader>
          <div>존</div>
          <div>센서 ID</div>
          <div>신호</div>
          <div>방향</div>
          <div>시간</div>
        </TableHeader>
        {stats.recentEvents.slice(0, 15).map((event, idx) => (
          <TableRow key={idx}>
            <ZoneBadge>{event.zone_id || '-'}</ZoneBadge>
            <SensorValue title={event.sensor_id}>{event.sensor_id?.substring(0, 20) || '-'}</SensorValue>
            <SignalBadge signal={event.signal}>
              {event.signal ? '활성' : '비활성'}
            </SignalBadge>
            <SensorValue>{event.direction || 'STOP'}</SensorValue>
            <SensorValue>
              {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : '미정'}
            </SensorValue>
          </TableRow>
        ))}
      </Table>

      {stats.recentEvents.length === 0 && !isLoading && (
        <Card style={{ textAlign: 'center' }}>
          <CardSubtext>아직 센서 이벤트가 없습니다</CardSubtext>
        </Card>
      )}
    </PageContainer>
  );
};

export default RealtimeMonitoringPage;
