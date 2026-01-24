import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Play, Pause, RefreshCw, Truck, PlusCircle } from 'lucide-react';
import axios from 'axios';

const PageContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
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
`;

const Title = styled.h1`
  font-size: 24px;
  font-weight: 900;
  color: ${props => props.theme.colors.text.main};
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const Controls = styled.div`
  display: flex;
  gap: 12px;
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background-color: ${props => props.$variant === 'primary' ? '#3b82f6' : '#6b7280'};
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const NumberInput = styled.input`
  width: 70px;
  padding: 10px;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 8px;
  background-color: ${props => props.theme.colors.surface};
  color: ${props => props.theme.colors.text.main};
  font-weight: 700;
  text-align: center;
  outline: none;
  font-size: 14px;
`;

const VisualizationContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const ZoneContainer = styled.div`
  background-color: ${props => props.theme.colors.surface};
  border: 2px solid ${props => props.theme.colors.border};
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
`;

const ZoneTitle = styled.div`
  font-size: 16px;
  font-weight: 900;
  color: ${props => props.theme.colors.text.main};
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid ${props => props.theme.colors.primary};
`;

const ZoneInfo = styled.div`
  font-size: 11px;
  color: ${props => props.theme.colors.text.muted};
  margin-bottom: 12px;
`;

const LineContainer = styled.div`
  background-color: ${props => props.theme.colors.surfaceHighlight};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
  position: relative;
  height: 60px;

  &:last-child {
    margin-bottom: 0;
  }
`;

const LineName = styled.div`
  font-size: 11px;
  font-weight: 700;
  color: ${props => props.theme.colors.text.muted};
  position: absolute;
  top: 2px;
  left: 8px;
  z-index: 2;
`;

const LineTrack = styled.div`
  position: relative;
  height: 30px;
  background: linear-gradient(to right, #f3f4f6, #e5e7eb, #f3f4f6);
  border-radius: 4px;
  margin-top: 20px;
  overflow: hidden;
  border: 1px solid ${props => props.theme.colors.border};
`;

const Basket = styled.div`
  position: absolute;
  top: 50%;
  left: ${props => props.$position}%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 10px;
  font-weight: 700;
  transition: all 0.1s linear;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
  z-index: 10;
  cursor: pointer;

  &:hover {
    transform: translateY(-50%) scale(1.2);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.6);
  }
`;

const BasketInfo = styled.div`
  position: absolute;
  bottom: -25px;
  left: ${props => props.$position}%;
  transform: translateX(-50%);
  font-size: 10px;
  color: ${props => props.theme.colors.text.muted};
  white-space: nowrap;
  pointer-events: none;
`;

const Stats = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-top: 16px;
`;

const StatCard = styled.div`
  background-color: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 8px;
  padding: 12px;
  text-align: center;
`;

const StatLabel = styled.div`
  font-size: 10px;
  font-weight: 700;
  color: ${props => props.theme.colors.text.muted};
  text-transform: uppercase;
  margin-bottom: 4px;
`;

const StatValue = styled.div`
  font-size: 20px;
  font-weight: 900;
  color: ${props => props.theme.colors.primary};
`;

const BasketVisualizationPage = () => {
  const [zones, setZones] = useState([]);
  const [baskets, setBaskets] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [basketCount, setBasketCount] = useState(5);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [zonesRes, basketsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/zones`),
        axios.get(`${API_BASE_URL}/baskets`),
      ]);

      const zonesData = zonesRes.data || [];
      const basketsData = basketsRes.data;
      const baskets = basketsData.baskets || (Array.isArray(basketsData) ? basketsData : []);

      setZones(zonesData);
      setBaskets(baskets);
    } catch (err) {
      console.error('데이터 조회 실패:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // 초기 로드 시 시뮬레이터 실행 상태 확인 (버튼 상태 동기화)
  useEffect(() => {
    const checkSimulatorStatus = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/simulator/status`);
        if (res.data) {
          setAutoRefresh(res.data.running);
        }
      } catch (err) {
        console.error('시뮬레이터 상태 확인 실패:', err);
      }
    };
    checkSimulatorStatus();
  }, []);

  const handleCreateBasket = async () => {
    try {
      // 첫 번째 존(보통 입고) 찾기
      const targetZone = zones.length > 0 ? zones[0].zone_id : '01-IB';
      await axios.post(`${API_BASE_URL}/api/baskets/create`, {
        zone_id: targetZone,
        count: basketCount
      });
      fetchData(); // 데이터 즉시 갱신
      // alert(`${targetZone} 구역에 바스켓 5개가 투입되었습니다.`); // 너무 잦은 알림 방지
    } catch (error) {
      console.error('바스켓 생성 실패:', error);
      alert('바스켓 생성 중 오류가 발생했습니다.');
    }
  };

  const handleToggleSimulation = async () => {
    try {
      const endpoint = autoRefresh ? '/simulator/stop' : '/simulator/start';
      await axios.post(`${API_BASE_URL}${endpoint}`);
      
      // [추가] 시작 시 바스켓이 하나도 없으면 자동으로 5개 생성
      if (!autoRefresh && baskets.length === 0) {
        const targetZone = zones.length > 0 ? zones[0].zone_id : '01-IB';
        try {
          await axios.post(`${API_BASE_URL}/api/baskets/create`, {
            zone_id: targetZone,
            count: basketCount
          });
          console.log('시뮬레이션 시작과 함께 초기 바스켓 자동 생성');
        } catch (e) {
          console.error('자동 생성 실패', e);
        }
      }
      
      setAutoRefresh(!autoRefresh);
    } catch (error) {
      console.error('시뮬레이션 제어 실패:', error);
      alert('시뮬레이션 제어 중 오류가 발생했습니다.');
    }
  };

  useEffect(() => {
    fetchData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchData, 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // 존별 바스켓 그룹핑
  const basketsByZone = {};
  zones.forEach(zone => {
    basketsByZone[zone.zone_id] = {
      zone,
      baskets: baskets.filter(b => b.zone_id === zone.zone_id)
    };
  });

  // 통계 계산
  const stats = {
    totalBaskets: baskets.length,
    inTransit: baskets.filter(b => b.status === 'moving' || b.status === 'in_transit').length,
    arrived: baskets.filter(b => b.status === 'arrived').length,
    available: baskets.filter(b => b.status === 'available').length,
  };

  return (
    <PageContainer>
      <Header>
        <Title>
          <Truck size={28} color="#3b82f6" />
          바스켓 이동 시각화
        </Title>
        <Controls>
          <NumberInput 
            type="number" 
            min="1" 
            max="100" 
            value={basketCount} 
            onChange={(e) => setBasketCount(Math.max(1, parseInt(e.target.value) || 1))}
          />
          <Button $variant="primary" onClick={handleCreateBasket}>
            <PlusCircle size={16} />
            바스켓 투입
          </Button>
          <Button
            $variant="primary"
            onClick={handleToggleSimulation}
          >
            {autoRefresh ? <Pause size={16} /> : <Play size={16} />}
            {autoRefresh ? '일시 정지' : '재개'}
          </Button>
          <Button $variant="primary" onClick={fetchData} disabled={isLoading}>
            <RefreshCw size={16} style={{ animation: isLoading ? 'spin 1s linear infinite' : 'none' }} />
            새로고침
          </Button>
        </Controls>
      </Header>

      <Stats>
        <StatCard>
          <StatLabel>전체 바스켓</StatLabel>
          <StatValue>{stats.totalBaskets}</StatValue>
        </StatCard>
        <StatCard>
          <StatLabel>이동 중</StatLabel>
          <StatValue style={{ color: '#3b82f6' }}>{stats.inTransit}</StatValue>
        </StatCard>
        <StatCard>
          <StatLabel>도착함</StatLabel>
          <StatValue style={{ color: '#10b981' }}>{stats.arrived}</StatValue>
        </StatCard>
        <StatCard>
          <StatLabel>사용 가능</StatLabel>
          <StatValue style={{ color: '#6b7280' }}>{stats.available}</StatValue>
        </StatCard>
      </Stats>

      <VisualizationContainer>
        {zones.map((zone) => {
          const zoneBaskets = basketsByZone[zone.zone_id]?.baskets || [];
          const lines = zone.zone_lines || [];

          return (
            <ZoneContainer key={zone.zone_id}>
              <ZoneTitle>{zone.zone_id} - {zone.zone_name}</ZoneTitle>
              <ZoneInfo>
                라인: {lines.length}개 | 바스켓: {zoneBaskets.length}개 | 센서: {zone.sensors || 0}개
              </ZoneInfo>

              {lines.map((line) => {
                const lineBaskets = zoneBaskets.filter(
                  b => b.line_id === line.line_id
                );
                const lineLength = line.length || 300;

                return (
                  <div key={line.line_id}>
                    <LineContainer>
                      <LineName>{line.line_id}</LineName>
                      <LineTrack>
                        {lineBaskets.map((basket) => {
                          // 백엔드에서 계산된 progress_percent 사용
                          const positionPercent = basket.progress_percent || 0;
                          return (
                            <Basket
                              key={basket.basket_id}
                              $position={Math.min(positionPercent, 95)}
                              title={`${basket.basket_id} - ${basket.status}`}
                            >
                              {basket.basket_id.split('-').pop()}
                            </Basket>
                          );
                        })}
                      </LineTrack>
                      {lineBaskets.length > 0 && (
                        <BasketInfo $position={0}>
                          {lineBaskets.length}개 바스켓
                        </BasketInfo>
                      )}
                    </LineContainer>
                  </div>
                );
              })}
            </ZoneContainer>
          );
        })}
      </VisualizationContainer>
    </PageContainer>
  );
};

export default BasketVisualizationPage;
