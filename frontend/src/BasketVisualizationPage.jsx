import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Play, Pause, RotateCcw, Truck, PlusCircle } from 'lucide-react';
import axios from 'axios';

const PageContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
  background-color: ${props => props.theme.colors.background};
  min-height: 100vh;
  position: relative;
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

const SpeedSegment = styled.div`
  position: absolute;
  top: 0;
  left: ${props => props.$left}%;
  width: ${props => props.$width}%;
  height: 100%;
  background: ${props => {
    const speed = props.$speedModifier || 1.0;
    if (speed < 0.8) return 'rgba(251, 191, 36, 0.4)'; // 느림 - 노랑
    if (speed > 1.2) return 'rgba(16, 185, 129, 0.4)'; // 빠름 - 녹색
    return 'transparent'; // 보통
  }};
  pointer-events: none;
  z-index: 1;
`;

const SensorDot = styled.div`
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: ${props => props.$active ? '#ef4444' : 'rgba(200, 200, 200, 0.3)'};
  box-shadow: ${props => props.$active ? '0 0 6px #ef4444' : 'none'};
  z-index: 20;
  transition: background-color 0.1s, box-shadow 0.1s;
`;

const Basket = styled.div`
  position: absolute;
  top: 50%;
  left: ${props => props.$position}%;
  transform: translateY(-50%);
  width: ${props => props.$width || 0.5}%;  /* 실제 비율로 계산 */
  min-width: 12px;  /* 최소 시각적 크기 */
  height: 24px;
  background: linear-gradient(135deg, 
    ${props => props.$isBottleneck ? '#ef4444' : '#3b82f6'}, 
    ${props => props.$isBottleneck ? '#dc2626' : '#2563eb'});
  border: ${props => props.$isBottleneck ? '2px solid #dc2626' : 'none'};
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 10px;
  font-weight: 700;
  transition: all 0.1s linear;
  box-shadow: ${props => props.$isBottleneck 
    ? '0 0 12px rgba(239, 68, 68, 0.8)' 
    : '0 2px 8px rgba(59, 130, 246, 0.4)'};
  z-index: 10;
  cursor: pointer;

  &:hover {
    transform: translateY(-50%) scale(1.2);
    box-shadow: ${props => props.$isBottleneck 
      ? '0 0 16px rgba(239, 68, 68, 1)' 
      : '0 4px 12px rgba(59, 130, 246, 0.6)'};
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

const GuidePanel = styled.div`
  background: linear-gradient(135deg, ${props => props.theme.colors.surface} 0%, ${props => props.theme.colors.surfaceHighlight} 100%);
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 12px;
  padding: ${props => props.$isExpanded ? '16px 20px' : '12px 16px'};
  transition: all 0.3s ease;
  max-height: ${props => props.$isExpanded ? '600px' : '50px'};
  overflow: hidden;
`;

const GuidePanelHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  
  &:hover {
    opacity: 0.8;
  }
`;

const GuidePanelContent = styled.div`
  display: flex;
  gap: 32px;
  align-items: flex-start;
  flex-wrap: wrap;
  margin-top: ${props => props.$isExpanded ? '12px' : '0'};
  opacity: ${props => props.$isExpanded ? 1 : 0};
  transition: opacity 0.3s ease;
`;

const GuideTitle = styled.div`
  font-size: 13px;
  font-weight: 900;
  color: ${props => props.theme.colors.text.main};
  margin-bottom: 8px;
`;

const GuideItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: ${props => props.theme.colors.text.muted};
`;

const ColorBox = styled.div`
  width: 24px;
  height: 24px;
  border-radius: 4px;
  background: ${props => props.$color};
  border: 1px solid ${props => props.theme.colors.border};
  flex-shrink: 0;
`;

const RuleItem = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background-color: ${props => props.theme.colors.surface};
  border-radius: 8px;
  border: 1px solid ${props => props.theme.colors.border};
`;

const RuleNumber = styled.div`
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 12px;
  flex-shrink: 0;
  margin-top: 2px;
`;

const RuleText = styled.div`
  font-size: 11px;
  color: ${props => props.theme.colors.text.muted};
  line-height: 1.6;
  flex: 1;
`;

const Stats = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 10px;
  margin-top: 16px;
`;

const StatCard = styled.div`
  background-color: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 8px;
  padding: 8px 10px;
  text-align: center;
`;

const StatLabel = styled.div`
  font-size: 9px;
  font-weight: 700;
  color: ${props => props.theme.colors.text.muted};
  text-transform: uppercase;
  margin-bottom: 3px;
`;

const StatValue = styled.div`
  font-size: 18px;
  font-weight: 900;
  color: ${props => props.theme.colors.primary};
`;

const BottleneckContainer = styled.div`
  background-color: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  padding: 12px;
  margin-top: 16px;
`;

const BottleneckTitle = styled.div`
  font-size: 11px;
  font-weight: 900;
  color: #ef4444;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
`;

const BottleneckList = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
`;

const BottleneckItem = styled.div`
  background-color: ${props => props.theme.colors.surface};
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 10px;
  color: ${props => props.theme.colors.text.main};
  
  .zone-id {
    font-weight: 700;
    color: #ef4444;
  }
  
  .count {
    font-weight: 700;
    color: #ef4444;
    margin-left: 4px;
  }
`;

const BasketVisualizationPage = () => {
  const [zones, setZones] = useState([]);
  const [baskets, setBaskets] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [basketCount, setBasketCount] = useState(5);
  const [lineSpeedZones, setLineSpeedZones] = useState({});
  const [lineCapacities, setLineCapacities] = useState({});
  const [bottlenecksByZone, setBottlenecksByZone] = useState({});
  const [showGuide, setShowGuide] = useState(false); // 가이드 토글 상태

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [zonesRes, basketsRes, statusRes, bottlenecksRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/zones`),
        axios.get(`${API_BASE_URL}/baskets`),
        axios.get(`${API_BASE_URL}/simulator/status`),
        axios.get(`${API_BASE_URL}/bottlenecks`),
      ]);

      // zones API가 이제 {zones: [], line_capacities: {}} 형태로 반환
      const zonesData = zonesRes.data?.zones || zonesRes.data || [];
      const capacitiesData = zonesRes.data?.line_capacities || {};
      const basketsData = basketsRes.data;
      const baskets = basketsData.baskets || (Array.isArray(basketsData) ? basketsData : []);
      const speedZones = statusRes.data?.line_speed_zones || {};
      
      // 병목 데이터 처리
      const bottlenecks = bottlenecksRes.data || {};
      const bottlenecksMap = {};
      if (Array.isArray(bottlenecks)) {
        bottlenecks.forEach(item => {
          bottlenecksMap[item.zone_id] = item;
        });
      } else if (bottlenecks && typeof bottlenecks === 'object') {
        Object.keys(bottlenecks).forEach(zoneId => {
          bottlenecksMap[zoneId] = bottlenecks[zoneId];
        });
      }

      setZones(zonesData);
      setBaskets(baskets);
      setLineSpeedZones(speedZones);
      setLineCapacities(capacitiesData); // 라인 용량 정보 저장
      setBottlenecksByZone(bottlenecksMap); // 병목 정보 저장
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

  const handleReset = async () => {
    try {
      await axios.post(`${API_BASE_URL}/simulator/reset`);
      fetchData(); // 즉시 데이터 갱신
      alert('시뮬레이션이 초기화되었습니다.');
    } catch (error) {
      console.error('초기화 실패:', error);
      alert('초기화 중 오류가 발생했습니다.');
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
    totalBaskets: baskets.filter(b => b.status !== 'available').length,
    inTransit: baskets.filter(b => b.status === 'moving' || b.status === 'in_transit').length,
    stopped: baskets.filter(b => b.status === 'stopped').length,
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
            바스켓 투입 (+{basketCount})
          </Button>
          <Button
            $variant="primary"
            onClick={handleToggleSimulation}
          >
            {autoRefresh ? <Pause size={16} /> : <Play size={16} />}
            {autoRefresh ? '일시 정지' : '재개'}
          </Button>
          <Button onClick={handleReset}>
            <RotateCcw size={16} />
            초기화
          </Button>
        </Controls>
      </Header>

      <GuidePanel $isExpanded={showGuide}>
        <GuidePanelHeader onClick={() => setShowGuide(!showGuide)}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
            <span style={{ fontSize: '13px', fontWeight: '900' }}>
              {showGuide ? '📖 가이드 닫기' : '📖 가이드 보기'}
            </span>
          </div>
          <span style={{ fontSize: '18px', transition: 'transform 0.3s ease', transform: showGuide ? 'rotate(180deg)' : 'rotate(0deg)' }}>
            ▼
          </span>
        </GuidePanelHeader>

        <GuidePanelContent $isExpanded={showGuide}>
          <div>
            <GuideTitle>📊 시각화 가이드</GuideTitle>
            <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
              <GuideItem>
                <ColorBox $color="rgba(251, 191, 36, 0.5)" />
                <span><strong>느린 구간</strong> (0.5x 속도)</span>
              </GuideItem>
              <GuideItem>
                <ColorBox $color="rgba(229, 231, 235, 1)" />
                <span><strong>보통 구간</strong> (1.0x 속도)</span>
              </GuideItem>
              <GuideItem>
                <ColorBox $color="rgba(16, 185, 129, 0.5)" />
                <span><strong>빠른 구간</strong> (1.5x 속도)</span>
              </GuideItem>
              <GuideItem>
                <ColorBox $color="linear-gradient(135deg, #3b82f6, #2563eb)" />
                <span><strong>정상 바스켓</strong> (이동 중)</span>
              </GuideItem>
              <GuideItem>
                <ColorBox $color="linear-gradient(135deg, #ef4444, #dc2626)" />
                <span><strong>병목 바스켓</strong> (정지 상태)</span>
              </GuideItem>
            </div>
          </div>

          {/* 투입 규칙 섹션 추가 */}
          <div>
            <GuideTitle>📝 바스켓 투입 규칙</GuideTitle>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <RuleItem>
                <RuleNumber>1</RuleNumber>
                <RuleText>
                  <strong>순차 투입:</strong> 버튼 클릭 시 즉시 투입되지 않고, 
                  <span style={{color: '#3b82f6', fontWeight: 'bold'}}> 대기열</span>에 추가됩니다.
                </RuleText>
              </RuleItem>
              <RuleItem>
                <RuleNumber>2</RuleNumber>
                <RuleText>
                  <strong>라인 분산:</strong> 여러 라인이 있을 경우, 
                  <span style={{color: '#10b981', fontWeight: 'bold'}}> 혼잡도가 낮은</span> 라인부터 자동 배분됩니다.
                </RuleText>
              </RuleItem>
              <RuleItem>
                <RuleNumber>3</RuleNumber>
                <RuleText>
                  <strong>충돌 방지:</strong> 같은 라인에 
                  <span style={{color: '#f59e0b', fontWeight: 'bold'}}> 0.8초 간격</span>으로 투입되어 충돌을 방지합니다.
                </RuleText>
              </RuleItem>
              <RuleItem>
                <RuleNumber>4</RuleNumber>
                <RuleText>
                  <strong>용량 경고:</strong> 라인 용량이 
                  <span style={{color: '#ef4444', fontWeight: 'bold'}}> 80% 이상</span>일 경우 경고 메시지가 표시됩니다.
                </RuleText>
              </RuleItem>
              <RuleItem>
                <RuleNumber>5</RuleNumber>
                <RuleText>
                  <strong>구간별 속도:</strong> 바스켓은 각 구간의 속도 계수에 따라 
                  <span style={{color: '#8b5cf6', fontWeight: 'bold'}}> 가변 속도</span>로 이동합니다.
                </RuleText>
              </RuleItem>
            </div>
          </div>
        </GuidePanelContent>
      </GuidePanel>

      <Stats>
        <StatCard>
          <StatLabel>투입된 바스켓</StatLabel>
          <StatValue>{stats.totalBaskets}</StatValue>
        </StatCard>
        <StatCard>
          <StatLabel>이동 중</StatLabel>
          <StatValue style={{ color: '#3b82f6' }}>{stats.inTransit}</StatValue>
        </StatCard>
        <StatCard>
          <StatLabel>정지 (병목)</StatLabel>
          <StatValue style={{ color: '#ef4444' }}>{stats.stopped}</StatValue>
        </StatCard>
        <StatCard>
          <StatLabel>도착함</StatLabel>
          <StatValue style={{ color: '#10b981' }}>{stats.arrived}</StatValue>
        </StatCard>
        <StatCard>
          <StatLabel>투입 가능</StatLabel>
          <StatValue style={{ color: '#6b7280' }}>{stats.available}</StatValue>
        </StatCard>
      </Stats>

      {/* 병목 정보 섹션 - 이제 각 zone 옆에 표시됨 */}

      <VisualizationContainer>
        {zones.map((zone) => {
          const zoneBaskets = basketsByZone[zone.zone_id]?.baskets || [];
          const lines = zone.zone_lines || [];
          const zoneBottlenecks = bottlenecksByZone[zone.zone_id];

          return (
            <ZoneContainer key={zone.zone_id}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
                <ZoneTitle>{zone.zone_id} - {zone.zone_name}</ZoneTitle>
                {zoneBottlenecks && zoneBottlenecks.bottleneck_count > 0 && (
                  <div style={{ 
                    background: 'rgba(239, 68, 68, 0.1)', 
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '6px',
                    padding: '4px 10px',
                    fontSize: '12px',
                    fontWeight: '700',
                    color: '#ef4444',
                    whiteSpace: 'nowrap'
                  }}>
                    ⚠️ 병목: {zoneBottlenecks.bottleneck_count}개
                    {zoneBottlenecks.bottleneck_baskets && zoneBottlenecks.bottleneck_baskets.length > 0 && (
                      <div style={{ fontSize: '11px', fontWeight: '600', marginTop: '2px' }}>
                        {zoneBottlenecks.bottleneck_baskets.slice(0, 8).join(', ')}
                        {zoneBottlenecks.bottleneck_baskets.length > 8 && '...'}
                      </div>
                    )}
                  </div>
                )}
              </div>
              <ZoneInfo>
                라인: {lines.length}개 | 바스켓: {zoneBaskets.length}개 | 센서: {zone.sensors || 0}개
              </ZoneInfo>

              {lines.map((line) => {
                const lineBaskets = zoneBaskets.filter(
                  b => b.line_id === line.line_id
                );
                const lineLength = line.length || 300;
                const sensorsPerLine = Math.max(1, Math.floor((zone.sensors || 0) / (lines.length || 1)));
                const speedSegments = lineSpeedZones[line.line_id] || [];
                
                // 라인 용량 정보 가져오기
                const capacity = lineCapacities[line.line_id] || { current: 0, max: 20, percent: 0 };
                const isNearFull = capacity.percent >= 80;
                const isMedium = capacity.percent >= 60 && capacity.percent < 80;

                return (
                  <div key={line.line_id}>
                    <LineContainer>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <LineName>{line.line_id}</LineName>
                        {/* 라인 용량 표시 */}
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '8px',
                          fontSize: '10px',
                          fontWeight: '700'
                        }}>
                          <span style={{ 
                            color: isNearFull ? '#ef4444' : isMedium ? '#f59e0b' : '#10b981' 
                          }}>
                            {capacity.current}/{capacity.max}
                          </span>
                          <div style={{
                            width: '60px',
                            height: '6px',
                            backgroundColor: '#1f2937',
                            borderRadius: '3px',
                            overflow: 'hidden',
                            border: '1px solid #374151'
                          }}>
                            <div style={{
                              width: `${Math.min(capacity.percent, 100)}%`,
                              height: '100%',
                              backgroundColor: isNearFull ? '#ef4444' : isMedium ? '#f59e0b' : '#10b981',
                              transition: 'width 0.3s ease'
                            }} />
                          </div>
                          <span style={{ 
                            color: isNearFull ? '#ef4444' : isMedium ? '#f59e0b' : '#6b7280',
                            minWidth: '35px',
                            textAlign: 'right'
                          }}>
                            {capacity.percent.toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <LineTrack>
                        {/* 구간별 속도 오버레이 */}
                        {speedSegments.map((seg, idx) => {
                          const startPercent = (seg.start / lineLength) * 100;
                          const widthPercent = ((seg.end - seg.start) / lineLength) * 100;
                          return (
                            <SpeedSegment
                              key={idx}
                              $left={startPercent}
                              $width={widthPercent}
                              $speedModifier={seg.multiplier}
                              title={`구간 ${idx + 1}: ${seg.multiplier}x`}
                            />
                          );
                        })}
                        {Array.from({ length: sensorsPerLine }).map((_, idx) => {
                          const sensorPosPercent = ((idx + 1) / (sensorsPerLine + 1)) * 100;
                          const isActive = lineBaskets.some(b => 
                            Math.abs((b.progress_percent || 0) - sensorPosPercent) < 1.5
                          );
                          return (
                            <SensorDot 
                              key={`sensor-${idx}`}
                              style={{ left: `${sensorPosPercent}%` }}
                              $active={isActive}
                              title={`Sensor ${idx + 1}`}
                            />
                          );
                        })}
                        {lineBaskets.map((basket) => {
                          // 백엔드에서 계산된 progress_percent 사용
                          const positionPercent = basket.progress_percent || 0;
                          const isBottleneck = basket.is_bottleneck || basket.status === 'stopped';
                          // 바스켓 크기를 라인 길이 대비 실제 비율로 계산
                          const basketWidthPercent = basket.width_cm ? (basket.width_cm / 100 / lineLength) * 100 : 0.5;
                          return (
                            <Basket
                              key={basket.basket_id}
                              $position={Math.min(positionPercent, 95)}
                              $width={basketWidthPercent}
                              $isBottleneck={isBottleneck}
                              title={`${basket.basket_id} - ${basket.status}${isBottleneck ? ' (병목)' : ''}\n크기: ${basket.width_cm}cm (${basketWidthPercent.toFixed(2)}%)`}
                            >
                              {parseInt(basket.basket_id.split('-').pop())}
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
