import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Activity, Play, Pause, RefreshCw, TrendingUp, AlertCircle } from 'lucide-react';
import axios from 'axios';

const PageContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
  background-color: ${props => props.theme.colors.background};
  min-height: 100vh;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, ${props => props.theme.colors.surface} 0%, ${props => props.theme.colors.surfaceHighlight} 100%);
  border-radius: 12px;
  border: 1px solid ${props => props.theme.colors.border};
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
`;

const HeaderLeft = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

const Title = styled.h1`
  font-size: 24px;
  font-weight: 900;
  color: ${props => props.theme.colors.text.main};
  margin: 0;
`;

const Controls = styled.div`
  display: flex;
  gap: 12px;
  align-items: center;
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background-color: ${props => props.$variant === 'primary' ? '#3b82f6' : props.$variant === 'danger' ? '#ef4444' : '#6b7280'};
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px ${props => props.$variant === 'primary' ? 'rgba(59, 130, 246, 0.3)' : props.$variant === 'danger' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(107, 114, 128, 0.3)'};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: ${props => props.$active ? '#10b98166' : '#f3f4f666'};
  border: 1px solid ${props => props.$active ? '#10b981' : '#d1d5db'};
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  color: ${props => props.$active ? '#10b981' : '#6b7280'};

  &::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: currentColor;
    box-shadow: ${props => props.$active ? '0 0 8px currentColor' : 'none'};
  }
`;

const GridLayout = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
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
    box-shadow: 0 8px 16px rgba(59, 130, 246, 0.1);
    transform: translateY(-2px);
  }
`;

const CardLabel = styled.div`
  font-size: 11px;
  font-weight: 700;
  color: ${props => props.theme.colors.text.muted};
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
`;

const CardValue = styled.div`
  font-size: 36px;
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

const TableContainer = styled.div`
  background-color: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
`;

const TableHeader = styled.div`
  display: grid;
  grid-template-columns: 1fr 1.5fr 1.2fr 1fr 1.2fr;
  gap: 16px;
  padding: 16px 20px;
  background-color: ${props => props.theme.colors.surfaceHighlight};
  border-bottom: 2px solid ${props => props.theme.colors.border};
  font-weight: 700;
  font-size: 11px;
  color: ${props => props.theme.colors.text.muted};
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const TableRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1.5fr 1.2fr 1fr 1.2fr;
  gap: 16px;
  padding: 14px 20px;
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

const Badge = styled.span`
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  background-color: ${props => props.$color === 'green' ? '#10b98166' : props.$color === 'red' ? '#ef444466' : '#3b82f666'};
  color: ${props => props.$color === 'green' ? '#10b981' : props.$color === 'red' ? '#ef4444' : '#3b82f6'};
`;

const SensorValue = styled.span`
  font-size: 12px;
  font-weight: 600;
  color: ${props => props.theme.colors.text.main};
  word-break: break-all;
`;

const EmptyState = styled.div`
  padding: 40px;
  text-align: center;
  color: ${props => props.theme.colors.text.muted};

  svg {
    margin-bottom: 16px;
    opacity: 0.5;
  }

  p {
    font-size: 14px;
    margin: 0;
  }
`;

const EnhancedRealtimeMonitoringPage = () => {
  const [stats, setStats] = useState({
    totalBaskets: 0,
    movingBaskets: 0,
    totalSensors: 0,
    activeSignals: 0,
    zones: [],
    recentEvents: [],
  });
  const [isLoading, setIsLoading] = useState(false);
  const [simulatorActive, setSimulatorActive] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [basketsRes, eventsRes, zonesRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/baskets`),
        axios.get(`${API_BASE_URL}/events/latest?count=20`),
        axios.get(`${API_BASE_URL}/zones`),
      ]);

      const basketData = basketsRes.data;
      const baskets = basketData.baskets || (Array.isArray(basketData) ? basketData : []);
      const movingBaskets = baskets.filter(b => b.status === 'moving' || b.status === 'in_transit').length;

      const eventsData = eventsRes.data;
      const events = eventsData.events || (Array.isArray(eventsData) ? eventsData : []);
      const activeSignals = events.filter(e => e.signal === true).length;

      const zones = zonesRes.data || (Array.isArray(zonesRes.data) ? zonesRes.data : []);
      const totalSensors = zones.reduce((sum, zone) => sum + (zone.sensors || 0), 0);

      setStats({
        totalBaskets: baskets.length,
        movingBaskets,
        totalSensors,
        activeSignals,
        zones,
        recentEvents: events,
      });

      setLastUpdate(new Date());
    } catch (err) {
      console.error('데이터 조회 실패:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSimulatorToggle = async () => {
    try {
      const endpoint = simulatorActive ? '/simulator/stop' : '/simulator/start';
      await axios.post(`${API_BASE_URL}${endpoint}`);
      setSimulatorActive(!simulatorActive);
      setTimeout(fetchData, 1000);
    } catch (err) {
      console.error('시뮬레이터 제어 실패:', err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <PageContainer>
      <Header>
        <HeaderLeft>
          <Activity size={28} color="#3b82f6" />
          <Title>실시간 모니터링 대시보드</Title>
        </HeaderLeft>
        <Controls>
          <Button
            $variant={simulatorActive ? 'danger' : 'primary'}
            onClick={handleSimulatorToggle}
            disabled={isLoading}
          >
            {simulatorActive ? (
              <>
                <Pause size={16} />
                중지
              </>
            ) : (
              <>
                <Play size={16} />
                시작
              </>
            )}
          </Button>
          <Button $variant="primary" onClick={fetchData} disabled={isLoading}>
            <RefreshCw size={16} style={{ animation: isLoading ? 'spin 1s linear infinite' : 'none' }} />
            새로고침
          </Button>
          <StatusIndicator $active={simulatorActive}>
            {simulatorActive ? '활성' : '대기'}
          </StatusIndicator>
        </Controls>
      </Header>

      <GridLayout>
        <Card>
          <CardLabel>전체 바스켓</CardLabel>
          <CardValue>{stats.totalBaskets}</CardValue>
          <CardSubtext>
            <TrendingUp size={14} />
            {stats.movingBaskets}개 이동 중
          </CardSubtext>
        </Card>

        <Card>
          <CardLabel>활성 신호</CardLabel>
          <CardValue>{stats.activeSignals}</CardValue>
          <CardSubtext>
            센서 감지율: {stats.totalSensors > 0 ? Math.round((stats.activeSignals / stats.totalSensors) * 100) : 0}%
          </CardSubtext>
        </Card>

        <Card>
          <CardLabel>센서 총개수</CardLabel>
          <CardValue>{stats.totalSensors}</CardValue>
          <CardSubtext>
            존: {stats.zones.length}개
          </CardSubtext>
        </Card>

        <Card>
          <CardLabel>마지막 업데이트</CardLabel>
          <CardValue style={{ fontSize: '16px' }}>
            {lastUpdate.toLocaleTimeString()}
          </CardValue>
          <CardSubtext>
            {Math.round((new Date() - lastUpdate) / 1000)}초 전
          </CardSubtext>
        </Card>
      </GridLayout>

      {!simulatorActive && (
        <Card style={{ backgroundColor: '#fef3c766', borderColor: '#f59e0b', padding: '16px' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'start' }}>
            <AlertCircle size={20} color="#f59e0b" style={{ marginTop: '2px', flexShrink: 0 }} />
            <div>
              <div style={{ fontWeight: 700, color: '#d97706', fontSize: '13px' }}>
                센서 시뮬레이터가 대기 중입니다
              </div>
              <div style={{ color: '#b45309', fontSize: '12px', marginTop: '4px' }}>
                우측의 "시작" 버튼을 클릭하여 실시간 센서 데이터 생성을 시작하세요.
              </div>
            </div>
          </div>
        </Card>
      )}

      <TableContainer>
        <TableHeader>
          <div>Zone</div>
          <div>센서 ID</div>
          <div>신호</div>
          <div>방향</div>
          <div>시간</div>
        </TableHeader>
        {stats.recentEvents && stats.recentEvents.length > 0 ? (
          stats.recentEvents.slice(0, 15).map((event, idx) => (
            <TableRow key={idx}>
              <Badge $color="blue">{event.zone_id || '-'}</Badge>
              <SensorValue title={event.sensor_id}>{event.sensor_id?.substring(0, 25) || '-'}</SensorValue>
              <Badge $color={event.signal ? 'green' : 'red'}>
                {event.signal ? '활성' : '비활성'}
              </Badge>
              <SensorValue>{event.direction || 'STOP'}</SensorValue>
              <SensorValue>
                {event.timestamp ? new Date(event.timestamp).toLocaleTimeString('ko-KR') : '-'}
              </SensorValue>
            </TableRow>
          ))
        ) : (
          <TableRow>
            <div colSpan={5} style={{ gridColumn: '1 / -1' }}>
              <EmptyState>
                <AlertCircle size={32} />
                <p>센서 이벤트 데이터가 없습니다</p>
                <p style={{ fontSize: '11px', marginTop: '8px' }}>시뮬레이터를 시작하면 데이터가 나타납니다</p>
              </EmptyState>
            </div>
          </TableRow>
        )}
      </TableContainer>
    </PageContainer>
  );
};

export default EnhancedRealtimeMonitoringPage;
