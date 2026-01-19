import React, { useState, useMemo, useEffect } from 'react';
import styled from 'styled-components';
import { Plus, Edit, Trash2, X, Save, Box, Minus, Settings, AlertTriangle, BarChart3 } from 'lucide-react';
import { apiService } from './api';

// --- [Styled Components] ---

const PageContainer = styled.div`
  color: ${props => props.theme.colors.text.main};
  animation: fadeIn 0.5s ease-out;
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;

const PageHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`;

const PresetContainer = styled.div`
  display: flex;
  gap: 12px;
  margin: 32px 0;
  align-items: center;
`;

const PresetLabel = styled.p`
  font-size: 14px;
  font-weight: 700;
  color: ${props => props.theme.colors.text.muted};
`;

const PresetButton = styled.button`
  background-color: ${props => props.theme.colors.surface};
  color: ${props => props.theme.colors.text.sub};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius};
  padding: 8px 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background-color: ${props => props.theme.colors.primary};
    color: #fff;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const PageTitle = styled.h2`
  font-size: 32px;
  font-weight: 900;
  color: ${props => props.theme.colors.text.main};
  span {
    color: ${props => props.theme.colors.primary};
  }
`;

const AddButton = styled.button`
  background-color: ${props => props.theme.colors.primary};
  color: #fff;
  border: none;
  border-radius: ${props => props.theme.borderRadius};
  padding: 12px 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    opacity: 0.9;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
  }
`;

const ZoneListContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
  margin-bottom: 48px;
`;

// 그래프 컨테이너
const ChartSection = styled.div`
  margin-top: 48px;
  padding-top: 32px;
  padding-bottom: 32px;
  border-top: 1px solid ${props => props.theme.colors.border};
`;

const ChartTitle = styled.h3`
  font-size: 24px;
  font-weight: 900;
  color: ${props => props.theme.colors.text.main};
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const ChartGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
`;

const ChartCard = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
`;

const ChartCardTitle = styled.h4`
  font-size: 11px;
  font-weight: 800;
  color: ${props => props.theme.colors.text.muted};
  margin: 0 0 8px 0;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  flex-shrink: 0;
`;

const BarChartContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 4px;
`;

const BarRow = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  min-height: 20px;
`;

const BarLabel = styled.div`
  min-width: 70px;
  max-width: 70px;
  font-size: 11px;
  font-weight: 700;
  color: ${props => props.theme.colors.text.sub};
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: right;
`;

const BarTrack = styled.div`
  flex: 1;
  height: 12px;
  background: ${props => props.theme.colors.background};
  border-radius: 4px;
  position: relative;
  overflow: hidden;
`;

const BarFill = styled.div`
  height: 100%;
  background: ${props => props.theme.colors.primary};
  width: ${props => props.width}%;
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 6px;
  font-size: 10px;
  font-weight: 800;
  color: white;
`;

const ZoneCard = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: ${props => props.theme.colors.primary};
    transform: translateY(-4px);
  }
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  font-size: 18px;
  font-weight: 700;
  color: ${props => props.theme.colors.text.main};
  
  .icon {
    color: ${props => props.theme.colors.primary};
  }
`;

const CardBody = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const InfoRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: ${props => props.theme.colors.text.muted};
  
  span:last-child {
    font-weight: 700;
    font-family: 'monospace';
    color: ${props => props.theme.colors.text.main};
    font-size: 16px;
  }
`;

const CardFooter = styled.div`
  display: flex;
  gap: 12px;
  margin-top: auto;
`;

const ActionButton = styled.button`
  flex: 1;
  padding: 10px;
  border-radius: ${props => props.theme.borderRadius};
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
  
  &.edit {
    background: ${props => props.theme.colors.surfaceHighlight};
    border: 1px solid ${props => props.theme.colors.border};
    color: ${props => props.theme.colors.text.sub};
    &:hover { background: ${props => props.theme.colors.border}; }
  }
  
  &.delete {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: ${props => props.theme.colors.status.danger};
    &:hover { background: rgba(239, 68, 68, 0.2); }
  }
`;

const FormContainer = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
`;

const Form = styled.form`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 16px;
  padding: 32px;
  width: 100%;
  max-width: 500px;
  position: relative;
  
  h3 {
    font-size: 20px;
    font-weight: 700;
    margin: 0 0 24px 0;
  }
`;

const CloseButton = styled.button`
  position: absolute;
  top: 16px;
  right: 16px;
  background: transparent;
  border: none;
  color: ${props => props.theme.colors.text.muted};
  cursor: pointer;
`;

const InputGroup = styled.div`
  margin-bottom: 20px;
`;

const Label = styled.label`
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: ${props => props.theme.colors.text.muted};
  margin-bottom: 8px;
`;

const Input = styled.input`
  width: 100%;
  background-color: ${props => props.theme.colors.background};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: 8px;
  padding: 12px;
  color: ${props => props.theme.colors.text.main};
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
  
  &:focus {
    border-color: ${props => props.theme.colors.primary};
  }
`;

const ValidationError = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: ${props => props.theme.colors.status.warning};
  background-color: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 8px;
  padding: 10px;
  margin-top: 24px;
`;


// --- [Initial Data & Presets] ---
const presets = {
  mfc: [
    { id: 'MFC-PK', name: '도심 피킹', lines: 20, length: 300, sensors: 300 },
    { id: 'MFC-SO', name: '패킹/출고', lines: 20, length: 200, sensors: 200 },
  ],
  tc: [
    { id: 'TC-XD', name: '크로스도킹', lines: 40, length: 1500, sensors: 1500 },
  ],
  dc: [
    { id: 'DC-IB', name: '입고', lines: 40, length: 800, sensors: 800 },
    { id: 'DC-ST', name: '보관', lines: 100, length: 2000, sensors: 2000 },
    { id: 'DC-PK', name: '피킹', lines: 80, length: 1500, sensors: 1500 },
    { id: 'DC-OB', name: '출고', lines: 40, length: 800, sensors: 800 },
  ],
  megaFc: [
    { id: 'IB-01', name: '입고', lines: 40, length: 800, sensors: 800 },
    { id: 'IS-01', name: '검수', lines: 40, length: 600, sensors: 600 },
    { id: 'ST-RC', name: '랙 보관', lines: 200, length: 3000, sensors: 3000 },
    { id: 'PK-01', name: '피킹', lines: 120, length: 2000, sensors: 2000 },
    { id: 'PC-01', name: '가공', lines: 30, length: 1000, sensors: 1000 },
    { id: 'SR-01', name: '분류', lines: 80, length: 1500, sensors: 1500 },
    { id: 'OB-01', name: '출고', lines: 40, length: 1200, sensors: 1200 },
  ],
  superFc: [
    { id: 'SFC-IB', name: '입고', lines: 60, length: 1000, sensors: 1000 },
    { id: 'SFC-IS', name: '검수', lines: 60, length: 800, sensors: 800 },
    { id: 'SFC-ST', name: '대형 랙 보관', lines: 400, length: 4000, sensors: 4000 },
    { id: 'SFC-PK', name: '자동 피킹', lines: 200, length: 3000, sensors: 3000 },
    { id: 'SFC-PC', name: '가공/재작업', lines: 50, length: 1500, sensors: 1500 },
    { id: 'SFC-SR', name: '지능형 분류', lines: 150, length: 2000, sensors: 2000 },
    { id: 'SFC-OB', name: '출고/배송', lines: 80, length: 2000, sensors: 2000 },
    { id: 'SFC-RET', name: '반품 처리', lines: 40, length: 1000, sensors: 1000 },
  ],
  intlHub: [
    { id: 'IH-IB', name: '국제 입고', lines: 100, length: 2000, sensors: 2000 },
    { id: 'IH-CS', name: '통관/검사', lines: 80, length: 1500, sensors: 1500 },
    { id: 'IH-SR', name: '국제 분류', lines: 200, length: 2500, sensors: 2500 },
    { id: 'IH-EX', name: '수출 처리', lines: 120, length: 2000, sensors: 2000 },
    { id: 'IH-OB', name: '국제 출고', lines: 80, length: 1500, sensors: 1500 },
  ],
  autoFc: [
    { id: 'AF-SR', name: '자동 분류', lines: 300, length: 3000, sensors: 3000 },
    { id: 'AF-PK', name: '로봇 피킹', lines: 250, length: 2500, sensors: 2500 },
    { id: 'AF-RB', name: '로봇 팔 처리', lines: 100, length: 2000, sensors: 2000 },
    { id: 'AF-OB', name: '자동 출고', lines: 150, length: 2000, sensors: 2000 },
  ]
};

const initialZones = presets.megaFc;


const LogisticsRailSettingPage = () => {
  const [zones, setZones] = useState([]);
  const [editingZone, setEditingZone] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ id: '', name: '', lines: '', length: '', sensors: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // 초기 zones 로드
  useEffect(() => {
    const loadZones = async () => {
      try {
        const data = await apiService.getZonesConfig();
        if (data && data.length > 0) {
          // DB에서 로드 (zone_id를 id로 매핑)
          setZones(data.map(z => ({
            id: z.zone_id,
            name: z.name,
            lines: z.lines,
            length: z.length,
            sensors: z.sensors
          })));
        } else {
          // DB가 비어있으면 기본 preset 저장
          await apiService.setZonesBatch(initialZones.map(z => ({
            zone_id: z.id,
            name: z.name,
            lines: z.lines,
            length: z.length,
            sensors: z.sensors
          })));
          setZones(initialZones);
        }
        setError(null);
      } catch (error) {
        console.error('zones 로드 실패:', error);
        setError('설정을 불러올 수 없습니다. 서버 연결을 확인하세요.');
      } finally {
        setLoading(false);
      }
    };
    loadZones();
  }, []);
  
  // zones 변경 시 DB에 저장
  const saveZonesToDB = async (updatedZones) => {
    try {
      for (const zone of updatedZones) {
        // 1단계: 존 저장
        console.log('존 저장 시작:', zone.id);
        await apiService.createZone({
          zone_id: zone.id,
          name: zone.name,
          lines: zone.lines,
          length: zone.length,
          sensors: zone.sensors
        });
        console.log('존 저장 완료:', zone.id);

        // 2단계: 라인 생성 (존이 저장된 후)
        const lines = [];
        for (let i = 0; i < zone.lines; i++) {
          lines.push({
            zone_id: zone.id,
            line_id: String.fromCharCode(65 + i), // A, B, C, D...
            length: zone.length,
            sensors: Math.floor(zone.sensors / zone.lines)
          });
        }
        console.log('라인 저장 시작:', lines);
        // 라인 저장
        await apiService.createLines(lines);
        console.log('라인 저장 완료:', zone.id);
      }
    } catch (error) {
      console.error('zones 저장 실패:', error);
    }
  };
  
  const sensorError = useMemo(() => {
    const { length, sensors } = formData;
    if (!length || !sensors) return null;
    if (parseInt(sensors, 10) > parseInt(length, 10) * 2) {
      return `센서 개수 (${sensors})는 라인 길이 (${length}m)의 2배(${length * 2}개)를 초과할 수 없습니다.`;
    }
    return null;
  }, [formData]);

  // 그래프 데이터 계산
  const chartData = useMemo(() => {
    if (zones.length === 0) return { linesData: [], sensorsData: [], lengthData: [], sensorsPerLine: [] };
    
    const maxLines = Math.max(...zones.map(z => z.lines));
    const maxSensors = Math.max(...zones.map(z => z.sensors));
    const maxLength = Math.max(...zones.map(z => z.length));
    const maxSensorsPerLine = Math.max(...zones.map(z => z.sensors / z.lines));
    
    console.log(`[chartData] zones: ${zones.length}개, lines: ${zones.map(z => z.lines).join(', ')}`);
    
    return {
      linesData: zones.map(z => ({
        label: z.id,
        value: z.lines,
        percent: (z.lines / maxLines) * 100
      })),
      sensorsData: zones.map(z => ({
        label: z.id,
        value: z.sensors,
        percent: (z.sensors / maxSensors) * 100
      })),
      lengthData: zones.map(z => ({
        label: z.id,
        value: z.length,
        percent: (z.length / maxLength) * 100
      })),
      sensorsPerLine: zones.map(z => ({
        label: z.id,
        value: (z.sensors / z.lines).toFixed(1),
        percent: ((z.sensors / z.lines) / maxSensorsPerLine) * 100
      }))
    };
  }, [zones]);

  const handleAdd = () => {
    setEditingZone(null);
    setFormData({ id: '', name: '', lines: '', length: '', sensors: '' });
    setShowForm(true);
  };

  const handleEdit = (zone) => {
    setEditingZone(zone);
    setFormData(zone);
    setShowForm(true);
  };

  const handleDelete = async (zoneId) => {
    if (window.confirm(`정말로 '${zoneId}' 구획을 삭제하시겠습니까?`)) {
        const updatedZones = zones.filter(z => z.id !== zoneId);
        setZones(updatedZones);
        await saveZonesToDB(updatedZones);
    }
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (sensorError) {
      alert('입력 값을 확인해주세요.');
      return;
    }
    
    const processedData = {
        ...formData,
        lines: parseInt(formData.lines, 10),
        length: parseInt(formData.length, 10),
        sensors: parseInt(formData.sensors, 10),
    };

    let updatedZones;
    if (editingZone) { // Update
      updatedZones = zones.map(z => z.id === editingZone.id ? processedData : z);
    } else { // Create
      const newZone = { ...processedData, id: processedData.id || `ZN-${Date.now()}` };
      updatedZones = [...zones, newZone];
    }
    setZones(updatedZones);
    await saveZonesToDB(updatedZones);
    setShowForm(false);
  };


  const handlePresetClick = async (presetKey) => {
    // 확인 다이얼로그
    if (!window.confirm('물류센터 시설정보가 변경됩니다. 확인하시겠습니까?')) {
      return;
    }

    const newZones = presets[presetKey];
    setZones(newZones);
    
    // 프리셋 로드 시: 기존 존은 UPDATE, 새로운 존은 INSERT
    try {
      // 현재 DB의 모든 존 가져오기
      const currentData = await apiService.getZonesConfig();
      const existingZoneIds = new Set(currentData?.map(z => z.zone_id) || []);
      const newZoneIds = new Set(newZones.map(z => z.id));
      
      // 1단계: 새 프리셋의 존들 저장 (있으면 UPDATE, 없으면 INSERT)
      for (const zone of newZones) {
        const zoneData = {
          zone_id: zone.id,
          name: zone.name,
          lines: zone.lines,
          length: zone.length,
          sensors: zone.sensors
        };
        
        if (existingZoneIds.has(zone.id)) {
          // 존재하면 UPDATE
          console.log('존 업데이트:', zone.id);
          await apiService.updateZone(zone.id, zoneData);
        } else {
          // 없으면 INSERT
          console.log('존 생성:', zone.id);
          await apiService.createZone(zoneData);
        }

        // 2단계: 라인 생성 (존 저장 후)
        const lines = [];
        for (let i = 0; i < zone.lines; i++) {
          lines.push({
            zone_id: zone.id,
            line_id: String.fromCharCode(65 + i), // A, B, C, D...
            length: zone.length,
            sensors: Math.floor(zone.sensors / zone.lines)
          });
        }
        await apiService.createLines(lines);
      }
      
      // 2단계: 프리셋에 없는 기존 존 삭제
      for (const existingId of existingZoneIds) {
        if (!newZoneIds.has(existingId)) {
          console.log('존 삭제:', existingId);
          await apiService.deleteZone(existingId);
        }
      }
      
      console.log(`프리셋 '${presetKey}' 로드 완료`);
    } catch (error) {
      console.error('프리셋 로드 중 오류:', error);
    }
  };

  return (
    <PageContainer>
      <PageHeader>
        <PageTitle>Rail System <span>Configuration</span></PageTitle>
        <AddButton onClick={handleAdd}>
          <Plus size={18} />
          새 구획 추가
        </AddButton>
      </PageHeader>

      {/* 그래프 섹션 */}
      {!error && zones.length > 0 && (
      <ChartSection>
        <ChartTitle>
          <BarChart3 size={28} />
          구역별 통계 시각화
        </ChartTitle>
        
        <ChartGrid>
          {/* 라인 개수 그래프 */}
          <ChartCard>
            <ChartCardTitle>라인 개수 (Lines per Zone)</ChartCardTitle>
            <BarChartContainer>
              {chartData.linesData.map(item => (
                <BarRow key={item.label}>
                  <BarLabel>{item.label}</BarLabel>
                  <BarTrack>
                    <BarFill width={item.percent}>{item.value}</BarFill>
                  </BarTrack>
                </BarRow>
              ))}
            </BarChartContainer>
          </ChartCard>

          {/* 센서 개수 그래프 */}
          <ChartCard>
            <ChartCardTitle>센서 개수 (Sensors per Zone)</ChartCardTitle>
            <BarChartContainer>
              {chartData.sensorsData.map(item => (
                <BarRow key={item.label}>
                  <BarLabel>{item.label}</BarLabel>
                  <BarTrack>
                    <BarFill width={item.percent}>{item.value}</BarFill>
                  </BarTrack>
                </BarRow>
              ))}
            </BarChartContainer>
          </ChartCard>

          {/* 라인 길이 그래프 */}
          <ChartCard>
            <ChartCardTitle>라인 길이 (Length per Zone)</ChartCardTitle>
            <BarChartContainer>
              {chartData.lengthData.map(item => (
                <BarRow key={item.label}>
                  <BarLabel>{item.label}</BarLabel>
                  <BarTrack>
                    <BarFill width={item.percent}>{item.value}m</BarFill>
                  </BarTrack>
                </BarRow>
              ))}
            </BarChartContainer>
          </ChartCard>

          {/* 라인당 센서 밀도 그래프 */}
          <ChartCard>
            <ChartCardTitle>라인당 센서 밀도 (Sensors per Line)</ChartCardTitle>
            <BarChartContainer>
              {chartData.sensorsPerLine.map(item => (
                <BarRow key={item.label}>
                  <BarLabel>{item.label}</BarLabel>
                  <BarTrack>
                    <BarFill width={item.percent}>{item.value}</BarFill>
                  </BarTrack>
                </BarRow>
              ))}
            </BarChartContainer>
          </ChartCard>
        </ChartGrid>
      </ChartSection>
      )}

      <PresetContainer>
        <PresetLabel>기능별 프리셋:</PresetLabel>
        <PresetButton onClick={() => handlePresetClick('mfc')}>소형/도심 MFC</PresetButton>
        <PresetButton onClick={() => handlePresetClick('tc')}>통과형 센터 (TC)</PresetButton>
        <PresetButton onClick={() => handlePresetClick('dc')}>광역 배송 센터 (DC)</PresetButton>
        <PresetButton onClick={() => handlePresetClick('megaFc')}>메가 풀필먼트 (FC)</PresetButton>
        <PresetButton onClick={() => handlePresetClick('superFc')}>초대형 풀필먼트 (Super FC)</PresetButton>
        <PresetButton onClick={() => handlePresetClick('intlHub')}>국제 물류 허브</PresetButton>
        <PresetButton onClick={() => handlePresetClick('autoFc')}>자동화 물류센터</PresetButton>
      </PresetContainer>

      {error ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#ef4444' }}>
          <AlertTriangle size={48} style={{ marginBottom: '16px' }} />
          <h3>{error}</h3>
          <p style={{ marginTop: '8px', fontSize: '14px' }}>백엔드 서버와 데이터베이스 연결을 확인하세요.</p>
        </div>
      ) : (
        <ZoneListContainer>
          {zones.map(zone => (
            <ZoneCard key={zone.id}>
            <CardHeader>
              <span>{zone.name}</span>
              <span className='icon'><Box size={20} /></span>
            </CardHeader>
            <CardBody>
              <InfoRow><span>구획 ID</span> <span>{zone.id}</span></InfoRow>
              <InfoRow><span>라인 개수</span> <span>{zone.lines}</span></InfoRow>
              <InfoRow><span>라인 길이</span> <span>{zone.length} m</span></InfoRow>
              <InfoRow><span>센서 개수</span> <span>{zone.sensors}</span></InfoRow>
            </CardBody>
            <CardFooter>
              <ActionButton className="edit" onClick={() => handleEdit(zone)}><Edit size={14}/> 수정</ActionButton>
              <ActionButton className="delete" onClick={() => handleDelete(zone.id)}><Trash2 size={14}/> 삭제</ActionButton>
            </CardFooter>
          </ZoneCard>
        ))}
      </ZoneListContainer>
      )}

      {showForm && (
        <FormContainer>
          <Form onSubmit={handleSubmit}>
            <CloseButton type="button" onClick={() => setShowForm(false)}><X/></CloseButton>
            <h3>{editingZone ? '구획 정보 수정' : '새 구획 생성'}</h3>
            
            <InputGroup>
              <Label htmlFor="id">구획 ID</Label>
              <Input type="text" name="id" value={formData.id} onChange={handleFormChange} required disabled={!!editingZone} placeholder="e.g., PK-02"/>
            </InputGroup>

            <InputGroup>
              <Label htmlFor="name">구획 이름</Label>
              <Input type="text" name="name" value={formData.name} onChange={handleFormChange} required placeholder="e.g., Picking Zone Beta"/>
            </InputGroup>

            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px'}}>
              <InputGroup>
                <Label htmlFor="lines">라인 개수</Label>
                <Input type="number" name="lines" value={formData.lines} onChange={handleFormChange} required min="1"/>
              </InputGroup>
              <InputGroup>
                <Label htmlFor="length">라인 길이 (m)</Label>
                <Input type="number" name="length" value={formData.length} onChange={handleFormChange} required min="1"/>
              </InputGroup>
            </div>
            
            <InputGroup>
              <Label htmlFor="sensors">관측 센서 개수</Label>
              <Input type="number" name="sensors" value={formData.sensors} onChange={handleFormChange} required min="0"/>
            </InputGroup>

            {sensorError && (
              <ValidationError>
                <AlertTriangle size={20} />
                <span>{sensorError}</span>
              </ValidationError>
            )}

            <div style={{ display: 'flex', gap: '12px', marginTop: '32px' }}>
              <ActionButton as="button" type="button" className="edit" style={{flex: 1}} onClick={() => setShowForm(false)}>취소</ActionButton>
              <AddButton as="button" type="submit" style={{flex: 2}} disabled={!!sensorError}><Save size={16}/> 저장</AddButton>
            </div>
          </Form>
        </FormContainer>
      )}
    </PageContainer>
  );
};

export default LogisticsRailSettingPage;