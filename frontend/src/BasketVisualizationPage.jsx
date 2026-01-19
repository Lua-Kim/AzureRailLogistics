import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Play, Pause, RefreshCw, Truck } from 'lucide-react';
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
  const [animationTime, setAnimationTime] = useState(0);

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

  useEffect(() => {
    fetchData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchData, 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  // 애니메이션 효과
  useEffect(() => {
    const animationInterval = setInterval(() => {
      setAnimationTime(t => (t + 1) % 100);
    }, 100);
    return () => clearInterval(animationInterval);
  }, []);

  // 바스켓에 시뮬레이션 위치 및 라인 분포 추가 (시간에 따라 변동)
  const enhancedBaskets = baskets.map((basket, idx) => {
    // 랜덤하게 존 할당
    const randomZone = zones.length > 0 ? zones[Math.floor(Math.random() * zones.length)] : null;
    const lineList = randomZone && randomZone.zone_lines ? randomZone.zone_lines : [];
    // 랜덤하게 라인 할당
    const randomLineObj = lineList.length > 0 ? lineList[Math.floor(Math.random() * lineList.length)] : null;
    const lineLength = randomLineObj ? randomLineObj.length : 100;
    // 바스켓 시작 위치를 균등 분포시키고, 시간에 따라 전체 구간을 따라 이동
    const start = (idx / baskets.length) * lineLength;
    const position = (start + animationTime * (lineLength / 100)) % lineLength;
    return {
      ...basket,
      zone_id: randomZone ? randomZone.zone_id : basket.zone_id,
      line_id: randomLineObj ? randomLineObj.line_id : basket.line_id,
      position
    };
  });

  // 존별 바스켓 그룹핑
  const basketsByZone = {};
  zones.forEach(zone => {
    basketsByZone[zone.zone_id] = {
      zone,
      baskets: enhancedBaskets.filter(b => b.zone_id === zone.zone_id)
    };
  });

  // 통계 계산
  const stats = {
    totalBaskets: enhancedBaskets.length,
    inTransit: enhancedBaskets.filter(b => b.status === 'moving' || b.status === 'in_transit').length,
    arrived: enhancedBaskets.filter(b => b.status === 'arrived').length,
    available: enhancedBaskets.filter(b => b.status === 'available').length,
  };

  return (
    <PageContainer>
      <Header>
        <Title>
          <Truck size={28} color="#3b82f6" />
          바스켓 이동 시각화
        </Title>
        <Controls>
          <Button
            $variant="primary"
            onClick={() => setAutoRefresh(!autoRefresh)}
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
                          // position: 0~lineLength 범위에서 움직임, CSS left는 0~100%로 변환
                          const posValue = basket.position ? basket.position : 0;
                          const positionPercent = lineLength > 0 ? (posValue / lineLength) * 100 : 0;
                          return (
                            <Basket
                              key={basket.basket_id}
                              $position={Math.min(positionPercent, 95)}
                              title={`${basket.basket_id} - ${basket.status}`}
                            >
                              {zoneBaskets.indexOf(basket) + 1}
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
