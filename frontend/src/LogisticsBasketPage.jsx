import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import { Filter } from 'lucide-react';

const PageContainer = styled.div`
  display: flex;
  gap: 0;
  background-color: ${props => props.theme.colors.background};
  min-height: 100vh;
  color: ${props => props.theme.colors.text.main};
`;

const MainContent = styled.div`
  flex: 1;
  padding: 20px;
  overflow-y: auto;
`;

const RightSidebar = styled.div`
  width: 280px;
  background-color: ${props => props.theme.colors.surface};
  border-left: 1px solid ${props => props.theme.colors.border};
  padding: 20px;
  overflow-y: auto;
  flex-shrink: 0;
  box-sizing: border-box;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);

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
  font-size: 14px;
  font-weight: 700;
  color: ${props => props.theme.colors.text.main};
  margin: 0 0 20px 0;
`;

const SidebarSection = styled.div`
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid ${props => props.theme.colors.border};

  &:last-child {
    border-bottom: none;
  }
`;

const SectionLabel = styled.label`
  display: block;
  font-size: 11px;
  font-weight: 700;
  color: ${props => props.theme.colors.text.muted};
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const SectionValue = styled.div`
  font-size: 13px;
  font-weight: 600;
  color: ${props => props.theme.colors.text.main};
  margin-bottom: 8px;
`;

const Slider = styled.input`
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(to right, ${props => props.theme.colors.border} 0%, ${props => props.theme.colors.primary} 100%);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  margin-top: 8px;

  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: ${props => props.theme.colors.primary};
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.4);
  }

  &::-moz-range-thumb {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: ${props => props.theme.colors.primary};
    cursor: pointer;
    border: none;
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.4);
  }
`;

const SelectInput = styled.select`
  width: 100%;
  padding: 8px;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 4px;
  font-size: 13px;
  color: ${props => props.theme.colors.text.main};
  background-color: ${props => props.theme.colors.surface};
  cursor: pointer;
  margin-top: 8px;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: ${props => props.theme.colors.text.sub};
  cursor: pointer;
  margin-top: 8px;

  input {
    cursor: pointer;
    width: 16px;
    height: 16px;
    accent-color: ${props => props.theme.colors.primary};
  }
`;

const InfoBox = styled.div`
  background: ${props => props.theme.colors.surfaceHighlight};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 6px;
  padding: 12px;
  font-size: 12px;
  color: ${props => props.theme.colors.text.muted};
  line-height: 1.5;
  margin-top: 8px;
`;

const Header = styled.div`
  background: ${props => props.theme.colors.surface};
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid ${props => props.theme.colors.border};
`;

const Title = styled.h1`
  margin: 0 0 10px 0;
  color: ${props => props.theme.colors.text.main};
  font-size: 28px;
`;

const Stats = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin-top: 15px;
`;

const StatBox = styled.div`
  background: ${props => props.theme.colors.primary};
  padding: 15px 25px;
  border-radius: 8px;
  color: white;
  
  .label {
    font-size: 12px;
    opacity: 0.9;
  }
  
  .value {
    font-size: 24px;
    font-weight: bold;
    margin-top: 5px;
  }
`;

const ZoneStats = styled.div`
  background: ${props => props.theme.colors.surface};
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid ${props => props.theme.colors.border};
`;

const ZoneStatsTitle = styled.h2`
  margin: 0 0 15px 0;
  color: ${props => props.theme.colors.text.main};
  font-size: 20px;
`;

const ZoneLineTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  
  thead {
    background: ${props => props.theme.colors.surfaceHighlight};
    
    th {
      padding: 10px 12px;
      text-align: left;
      font-weight: 600;
      color: ${props => props.theme.colors.text.main};
      border-bottom: 2px solid ${props => props.theme.colors.border};
      font-size: 14px;
    }
  }
  
  tbody {
    tr {
      border-bottom: 1px solid ${props => props.theme.colors.border};
      
      &:hover {
        background-color: ${props => props.theme.colors.surfaceHighlight};
      }
      
      td {
        padding: 10px 12px;
        color: ${props => props.theme.colors.text.main};
        font-size: 14px;
      }
    }
  }
`;

const CountBadge = styled.span`
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  background: ${props => props.theme.colors.status.success};
  color: white;
`;

const ControlPanel = styled.div`
  background: ${props => props.theme.colors.surface};
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid ${props => props.theme.colors.border};
`;

const FilterButtons = styled.div`
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 15px;
`;

const FilterButton = styled.button`
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: ${props => props.active ? props.theme.colors.primary : props.theme.colors.surfaceHighlight};
  color: ${props => props.active ? 'white' : props.theme.colors.text.main};
  border: 1px solid ${props => props.theme.colors.border};
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }
`;

const AssignForm = styled.div`
  padding-top: 15px;
  border-top: 2px solid ${props => props.theme.colors.border};
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
  align-items: end;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  
  label {
    font-size: 12px;
    color: ${props => props.theme.colors.text.main};
    margin-bottom: 5px;
    font-weight: 500;
  }
  
  input {
    padding: 8px;
    border: 1px solid ${props => props.theme.colors.border};
    border-radius: 4px;
    font-size: 14px;
    background-color: ${props => props.theme.colors.surface};
    color: ${props => props.theme.colors.text.main};
    
    &:focus {
      outline: none;
      border-color: ${props => props.theme.colors.primary};
    }
  }
`;

const AssignButton = styled.button`
  padding: 8px 20px;
  background: ${props => props.theme.colors.primary};
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const TableContainer = styled.div`
  background: ${props => props.theme.colors.surface};
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
  border: 1px solid ${props => props.theme.colors.border};
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  
  thead {
    background: ${props => props.theme.colors.surfaceHighlight};
    
    th {
      padding: 12px;
      text-align: left;
      font-weight: 600;
      color: ${props => props.theme.colors.text.main};
      border-bottom: 2px solid ${props => props.theme.colors.border};
      white-space: nowrap;
    }
  }
  
  tbody {
    tr {
      border-bottom: 1px solid ${props => props.theme.colors.border};
      transition: background-color 0.2s;
      
      &:hover {
        background-color: ${props => props.theme.colors.surfaceHighlight};
      }
      
      td {
        padding: 12px;
        color: ${props => props.theme.colors.text.main};
      }
    }
  }
`;

const StatusBadge = styled.span`
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background-color: ${props => {
    if (props.status === 'in_transit') return '#ffc107';
    if (props.status === 'arrived') return props.theme.colors.status.success;
    return props.theme.colors.text.muted;
  }};
  color: white;
  white-space: nowrap;
`;

const LoadingText = styled.div`
  text-align: center;
  padding: 40px;
  font-size: 18px;
  color: ${props => props.theme.colors.text.muted};
`;

const ErrorText = styled.div`
  text-align: center;
  padding: 40px;
  font-size: 18px;
  color: ${props => props.theme.colors.status.danger};
`;

const EmptyMessage = styled.p`
  color: ${props => props.theme.colors.text.muted};
  text-align: center;
  padding: 20px 0;
  margin: 0;
`;

const BasketPoolPage = () => {
  const [baskets, setBaskets] = useState([]);
  const [filteredBaskets, setFilteredBaskets] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  
  // 우측 사이드바 설정
  const [zones, setZones] = useState([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [defaultZone, setDefaultZone] = useState('all');
  const [defaultLine, setDefaultLine] = useState('');
  const [poolSize, setPoolSize] = useState(100);

  // zones 데이터 조회
  useEffect(() => {
    const fetchZones = async () => {
      try {
        const response = await axios.get('http://localhost:8000/zones/config');
        console.log('zones 데이터 받아옴:', response.data);
        setZones(response.data);
        // 기본값을 'all'로 설정 (전체 존 조회)
      } catch (err) {
        console.error('Failed to fetch zones:', err);
      }
    };
    fetchZones();
  }, []);

  // 기본 존이 변경될 때 기본 라인도 자동 업데이트
  useEffect(() => {
    if (defaultZone === 'all') {
      setDefaultLine('');
    } else {
      const selectedZone = zones.find(z => z.zone_id === defaultZone);
      if (selectedZone && selectedZone.zone_lines && selectedZone.zone_lines.length > 0) {
        setDefaultLine(selectedZone.zone_lines[0].line_id);
      }
    }
  }, [defaultZone, zones]);

  useEffect(() => {
    fetchBaskets();
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchBaskets, refreshInterval * 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, refreshInterval]);

  useEffect(() => {
    filterBaskets();
  }, [baskets, statusFilter]);

  const fetchBaskets = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/baskets');
      const { baskets: basketList, statistics: stats } = response.data;
      
      setBaskets(basketList);
      setStatistics(stats);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch baskets:', err);
      setError('바스켓 데이터를 가져오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const filterBaskets = () => {
    if (statusFilter === 'all') {
      setFilteredBaskets(baskets);
    } else {
      setFilteredBaskets(baskets.filter(b => b.status === statusFilter));
    }
  };

  const handleAssign = async () => {
    if (!assignForm.basketId || !assignForm.zoneId || !assignForm.lineId || !assignForm.destination) {
      alert('모든 필드를 입력해주세요.');
      return;
    }

    try {
      const response = await axios.post('http://localhost:8000/baskets/assign', null, {
        params: assignForm
      });
      
      if (response.data.success) {
        alert('바스켓이 할당되었습니다.');
        setAssignForm({ basketId: '', zoneId: defaultZone, lineId: defaultLine, destination: '' });
        fetchBaskets();
      } else {
        alert('할당 실패: ' + response.data.error);
      }
    } catch (err) {
      console.error('Failed to assign basket:', err);
      alert('바스켓 할당 중 오류가 발생했습니다.');
    }
  };

  const getStatusText = (status) => {
    if (status === 'available') return '대기중';
    if (status === 'in_transit') return '운송중';
    if (status === 'arrived') return '도착';
    return status;
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleString('ko-KR');
  };

  return (
    <PageContainer>
      <MainContent>
        <Header>
          <Title>📊 Baskets Board</Title>
          <Stats>
            <StatBox>
              <div className="label">Total Baskets</div>
              <div className="value">{statistics?.total || 0}</div>
            </StatBox>
            <StatBox>
              <div className="label">Available</div>
              <div className="value">{statistics?.available || 0}</div>
            </StatBox>
            <StatBox>
              <div className="label">In Transit</div>
              <div className="value">{statistics?.in_transit || 0}</div>
            </StatBox>
            <StatBox>
              <div className="label">Arrived</div>
              <div className="value">{statistics?.arrived || 0}</div>
            </StatBox>
          </Stats>
        </Header>

        <ControlPanel>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', whiteSpace: 'nowrap' }}>
              <Filter size={18} style={{ opacity: 0.7 }} />
              <span style={{ fontSize: '14px', fontWeight: '600' }}>바스켓 상태 필터링</span>
            </div>
            <FilterButtons>
            <FilterButton active={statusFilter === 'all'} onClick={() => setStatusFilter('all')}>
              전체
            </FilterButton>
            <FilterButton active={statusFilter === 'available'} onClick={() => setStatusFilter('available')}>
              대기중
            </FilterButton>
            <FilterButton active={statusFilter === 'in_transit'} onClick={() => setStatusFilter('in_transit')}>
              운송중
            </FilterButton>
            <FilterButton active={statusFilter === 'arrived'} onClick={() => setStatusFilter('arrived')}>
              도착
            </FilterButton>
          </FilterButtons>
          </div>
        </ControlPanel>

        <TableContainer>
          {loading && <LoadingText>Loading baskets...</LoadingText>}
          {error && <ErrorText>{error}</ErrorText>}
          
          {!loading && !error && (
            <Table>
              <thead>
                <tr>
                  <th>No.</th>
                  <th>Basket ID</th>
                  <th>Zone</th>
                  <th>Line</th>
                  <th>Line Length (m)</th>
                  <th>Destination</th>
                  <th>Status</th>
                  <th>Assigned At</th>
                  <th>Updated At</th>
                </tr>
              </thead>
              <tbody>
                {filteredBaskets.map((basket, index) => (
                  <tr key={basket.basket_id}>
                    <td>{index + 1}</td>
                    <td>{basket.basket_id}</td>
                    <td>{basket.zone_id || '-'}</td>
                    <td>{basket.line_id || '-'}</td>
                    <td>{basket.line_length ? Math.floor(basket.line_length) : '-'}</td>
                    <td>{basket.destination || '-'}</td>
                    <td>
                      <StatusBadge status={basket.status}>
                        {getStatusText(basket.status)}
                      </StatusBadge>
                    </td>
                    <td>{formatTimestamp(basket.assigned_at)}</td>
                    <td>{formatTimestamp(basket.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </TableContainer>
      </MainContent>

      <RightSidebar>
        <SidebarTitle>⚙️ 바스켓 환경설정</SidebarTitle>

        <SidebarSection>
          <SectionLabel>Zone ID</SectionLabel>
          <SelectInput 
            value={defaultZone}
            onChange={(e) => {
              setDefaultZone(e.target.value);
            }}
          >
            <option value="all">🌐 전체</option>
            {zones.map((zone) => (
              <option key={zone.zone_id} value={zone.zone_id}>
                {zone.zone_id} ({zone.name})
              </option>
            ))}
          </SelectInput>
          <InfoBox>Line-LogisRail</InfoBox>

          <SelectInput 
            value={defaultLine}
            onChange={(e) => {
              setDefaultLine(e.target.value);
            }}
            style={{ marginTop: '10px' }}
            disabled={defaultZone === 'all'}
          >
            {defaultZone !== 'all' ? (
              zones
                .find(z => z.zone_id === defaultZone)?.zone_lines?.map((line) => (
                  <option key={line.line_id} value={line.line_id}>
                    {line.line_id}
                  </option>
                )) || null
            ) : (
              <option value="">전체 선택 시 비활성화</option>
            )}
          </SelectInput>
          <InfoBox>기본 라인 ID (선택된 존의 라인에 따라 동적으로 업데이트)</InfoBox>
        </SidebarSection>

        <SidebarSection>
          <SectionLabel>자동 새로고침</SectionLabel>
          <CheckboxLabel>
            <input 
              type="checkbox" 
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            활성화
          </CheckboxLabel>
          {autoRefresh && (
            <>
              <SectionLabel style={{ marginTop: '12px' }}>새로고침 간격 (초)</SectionLabel>
              <SectionValue>{refreshInterval}초</SectionValue>
              <Slider 
                type="range" 
                min="1" 
                max="30" 
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
              />
              <InfoBox>
                현재 {refreshInterval}초마다 자동으로 데이터를 새로고칩니다.
              </InfoBox>
            </>
          )}
        </SidebarSection>

        <SidebarSection>
          <SectionLabel>바스켓 풀 크기</SectionLabel>
          <SectionValue>{poolSize}개</SectionValue>
          <Slider 
            type="range" 
            min="50" 
            max="500" 
            step="10"
            value={poolSize}
            onChange={(e) => setPoolSize(parseInt(e.target.value))}
            disabled
          />
          <InfoBox>
            현재 풀 크기: {poolSize}개 (읽기 전용)
          </InfoBox>
        </SidebarSection>

        <SidebarSection>
          <SectionLabel>현황 요약</SectionLabel>
          <SectionValue>
            📊 총 바스켓: {statistics?.total || 0}
          </SectionValue>
          <SectionValue>
            ✅ 대기중: {statistics?.available || 0}
          </SectionValue>
          <SectionValue>
            🚚 운송중: {statistics?.in_transit || 0}
          </SectionValue>
          <SectionValue>
            🎯 도착: {statistics?.arrived || 0}
          </SectionValue>
        </SidebarSection>
      </RightSidebar>
    </PageContainer>
  );
};

export default BasketPoolPage;
