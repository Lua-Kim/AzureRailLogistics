import React, { useState, useMemo, useEffect } from 'react';
import styled from 'styled-components';
import { Plus, Edit, Trash2, X, Save, Box, Minus, Settings, AlertTriangle, BarChart3, HelpCircle, Info } from 'lucide-react';
import { apiService } from './api';

// --- [Styled Components] ---

const PageContainer = styled.div`
  color: ${props => props.theme.colors.text.main};
  padding: 32px;
  animation: fadeIn 0.5s ease-out;
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;

const GuideBox = styled.div`
  background-color: ${props => props.theme.colors.surfaceHighlight};
  border: 1px solid ${props => props.theme.colors.primary}40;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 32px;
  display: flex;
  gap: 16px;
  align-items: flex-start;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  
  .icon-wrapper {
    background-color: ${props => props.theme.colors.surface};
    padding: 10px;
    border-radius: 50%;
    color: ${props => props.theme.colors.primary};
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .content {
    flex: 1;
  }
  
  h4 {
    margin: 0 0 8px 0;
    font-size: 16px;
    font-weight: 800;
    color: ${props => props.theme.colors.text.main};
  }
  
  p {
    margin: 0 0 12px 0;
    font-size: 14px;
    color: ${props => props.theme.colors.text.sub};
    line-height: 1.5;
  }
  
  ul {
    margin: 0;
    padding-left: 20px;
    font-size: 14px;
    color: ${props => props.theme.colors.text.sub};
    
    li {
      margin-bottom: 4px;
      line-height: 1.4;
      
      strong {
        color: ${props => props.theme.colors.primary};
        font-weight: 700;
      }
      
      code {
        background-color: ${props => props.theme.colors.background};
        padding: 2px 6px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 12px;
        border: 1px solid ${props => props.theme.colors.border};
      }
    }
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

const GuideButton = styled.button`
  background: none;
  border: none;
  color: ${props => props.theme.colors.text.muted};
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  margin-left: 12px;
  
  &:hover { color: ${props => props.theme.colors.primary}; }
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
  position: relative;
  gap: 16px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: ${props => props.theme.colors.primary};
    transform: translateY(-4px);
  }
`;

const StepBadge = styled.div`
  position: absolute;
  top: -12px;
  left: -12px;
  width: 32px;
  height: 32px;
  background-color: ${props => props.theme.colors.primary};
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 16px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  z-index: 1;
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
    { id: '01-PK', name: '도심 피킹', lines: 20, length: 300, sensors: 300 },
    { id: '02-SO', name: '패킹/출고', lines: 20, length: 200, sensors: 200 },
  ],
  tc: [
    { id: '01-XD', name: '크로스도킹', lines: 40, length: 1500, sensors: 1500 },
  ],
  dc: [
    { id: '01-IB', name: '입고', lines: 40, length: 800, sensors: 800 },
    { id: '02-ST', name: '보관', lines: 100, length: 2000, sensors: 2000 },
    { id: '03-PK', name: '피킹', lines: 80, length: 1500, sensors: 1500 },
    { id: '04-OB', name: '출고', lines: 40, length: 800, sensors: 800 },
  ],
  megaFc: [
    { id: '01-IB', name: '입고', lines: 40, length: 800, sensors: 800 },
    { id: '02-IS', name: '검수', lines: 40, length: 600, sensors: 600 },
    { id: '03-ST', name: '랙 보관', lines: 200, length: 3000, sensors: 3000 },
    { id: '04-PK', name: '피킹', lines: 120, length: 2000, sensors: 2000 },
    { id: '05-PC', name: '가공', lines: 30, length: 1000, sensors: 1000 },
    { id: '06-SR', name: '분류', lines: 80, length: 1500, sensors: 1500 },
    { id: '07-OB', name: '출고', lines: 40, length: 1200, sensors: 1200 },
  ],
  superFc: [
    { id: '01-IB', name: '입고', lines: 60, length: 1000, sensors: 1000 },
    { id: '02-IS', name: '검수', lines: 60, length: 800, sensors: 800 },
    { id: '03-ST', name: '대형 랙 보관', lines: 400, length: 4000, sensors: 4000 },
    { id: '04-PK', name: '자동 피킹', lines: 200, length: 3000, sensors: 3000 },
    { id: '05-PC', name: '가공/재작업', lines: 50, length: 1500, sensors: 1500 },
    { id: '06-SR', name: '지능형 분류', lines: 150, length: 2000, sensors: 2000 },
    { id: '07-OB', name: '출고/배송', lines: 80, length: 2000, sensors: 2000 },
    { id: '08-RET', name: '반품 처리', lines: 40, length: 1000, sensors: 1000 },
  ],
  intlHub: [
    { id: '01-IB', name: '국제 입고', lines: 100, length: 2000, sensors: 2000 },
    { id: '02-CS', name: '통관/검사', lines: 80, length: 1500, sensors: 1500 },
    { id: '03-SR', name: '국제 분류', lines: 200, length: 2500, sensors: 2500 },
    { id: '04-EX', name: '수출 처리', lines: 120, length: 2000, sensors: 2000 },
    { id: '05-OB', name: '국제 출고', lines: 80, length: 1500, sensors: 1500 },
  ],
  autoFc: [
    { id: '01-SR', name: '자동 분류', lines: 300, length: 3000, sensors: 3000 },
    { id: '02-PK', name: '로봇 피킹', lines: 250, length: 2500, sensors: 2500 },
    { id: '03-RB', name: '로봇 팔 처리', lines: 100, length: 2000, sensors: 2000 },
    { id: '04-OB', name: '자동 출고', lines: 150, length: 2000, sensors: 2000 },
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
      // 개별 저장 대신 일괄 저장(Batch) API 사용으로 변경 (Shift 로직 등 대량 변경 대응)
      await apiService.setZonesBatch(updatedZones.map(z => ({
        zone_id: z.id,
        name: z.name,
        lines: z.lines,
        length: z.length,
        sensors: z.sensors
      })));
      console.log('✅ DB 저장 및 동기화 완료');
    } catch (error) {
      console.error('zones 저장 실패:', error);
      alert('서버 저장 중 오류가 발생했습니다. 변경 사항이 반영되지 않았을 수 있습니다.');
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

  // 존 정렬 로직 (백엔드와 동일하게 맞춤)
  const sortedZones = useMemo(() => {
    return [...zones].sort((a, b) => {
      const getScore = (zone) => {
        const zid = zone.id.toUpperCase();
        // 1. 숫자로 시작 (가장 우선)
        if (/^\d/.test(zid)) return 1;
        // 2. 물류 키워드
        if (zid.includes('IB')) return 2;
        if (zid.includes('SR')) return 3;
        if (zid.includes('OB')) return 4;
        // 3. 그 외
        return 5;
      };

      const scoreA = getScore(a);
      const scoreB = getScore(b);

      if (scoreA !== scoreB) return scoreA - scoreB;
      
      // 점수가 같으면 문자열 정렬 (숫자 인식 정렬)
      return a.id.localeCompare(b.id, undefined, { numeric: true, sensitivity: 'base' });
    });
  }, [zones]);

  const handleAdd = () => {
    setEditingZone(null);
    
    // 비어있는 가장 빠른 순번 찾기 (중간에 삭제된 번호가 있으면 채움)
    let nextNum = 1;
    const existingNums = new Set();
    
    zones.forEach(zone => {
      const match = zone.id.match(/^(\d+)/);
      if (match) {
        existingNums.add(parseInt(match[1], 10));
      }
    });

    while (existingNums.has(nextNum)) {
      nextNum++;
    }
    const nextIdPrefix = `${String(nextNum).padStart(2, '0')}-`; // "08-" 형태로 포맷팅

    setFormData({ id: nextIdPrefix, name: '', lines: '', length: '', sensors: '' });
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

    // ID에서 순번 추출
    const match = processedData.id.match(/^(\d+)-/);
    const targetNum = match ? parseInt(match[1], 10) : null;
    
    let finalZones = [...zones];

    // [새 구획 추가]이면서 [순번 충돌]이 발생할 경우 -> 밀어내기(Shift) 로직 수행
    if (!editingZone && targetNum !== null) {
      const conflict = zones.some(z => {
        const m = z.id.match(/^(\d+)-/);
        return m && parseInt(m[1], 10) === targetNum;
      });

      if (conflict) {
        if (window.confirm(`순번 ${targetNum}번 구획이 이미 존재합니다.\n\n기존 ${targetNum}번 이후의 구획들을 뒤로 밀고 이 구획을 삽입하시겠습니까?\n(취소 시 중복된 순번으로 추가됩니다)`)) {
          // Shift Logic: targetNum 이상인 존들의 ID 숫자 +1
          finalZones = zones.map(z => {
            const m = z.id.match(/^(\d+)(-.+)/); // 숫자와 나머지 분리 (예: "02", "-PK")
            if (m) {
              const currentNum = parseInt(m[1], 10);
              if (currentNum >= targetNum) {
                const newNum = currentNum + 1;
                const newId = `${String(newNum).padStart(2, '0')}${m[2]}`;
                return { ...z, id: newId };
              }
            }
            return z;
          });
        }
      }
    }

    if (editingZone) { // Update
      finalZones = finalZones.map(z => z.id === editingZone.id ? processedData : z);
    } else { // Create
      // ID 중복 최종 체크 (Shift 안 했을 경우 대비)
      if (finalZones.some(z => z.id === processedData.id)) {
        alert('이미 존재하는 구획 ID입니다. 다른 ID를 사용해주세요.');
        return;
      }
      finalZones = [...finalZones, processedData];
    }
    
    setZones(finalZones);
    await saveZonesToDB(finalZones);
    setShowForm(false);
  };


  const handlePresetClick = async (presetKey) => {
    // 확인 다이얼로그
    if (!window.confirm('물류센터 시설정보가 변경됩니다. 확인하시겠습니까?')) {
      return;
    }

    const newZones = presets[presetKey];
    setZones(newZones);
    
    try {
      // 일괄 저장 API를 사용하여 기존 데이터를 덮어쓰고 새 프리셋으로 교체
      await apiService.setZonesBatch(newZones.map(z => ({
        zone_id: z.id,
        name: z.name,
        lines: z.lines,
        length: z.length,
        sensors: z.sensors
      })));
      console.log(`프리셋 '${presetKey}' 로드 완료`);
    } catch (error) {
      console.error('프리셋 로드 중 오류:', error);
    }
  };

  return (
    <PageContainer>
      <GuideBox>
        <div className="icon-wrapper"><Info size={24} /></div>
        <div className="content">
          <h4>트래픽 흐름 설정 가이드</h4>
          <p>
            시뮬레이션에서 바스켓은 <strong>Zone ID의 정렬 순서</strong>에 따라 구역을 이동합니다. 
            물류 흐름이 끊기지 않도록 아래 규칙을 참고하여 ID를 설정하세요.
          </p>
          <ul>
            <li><strong>1순위 (권장):</strong> 숫자 접두어 사용 (예: <code>01-IB</code>, <code>02-SR</code>, <code>03-OB</code>)</li>
            <li><strong>2순위:</strong> 표준 물류 키워드 (<code>IB</code> 입고 → <code>SR</code> 보관 → <code>OB</code> 출고)</li>
            <li><strong>3순위:</strong> 그 외 알파벳 오름차순</li>
          </ul>
        </div>
      </GuideBox>

      <PageHeader>
        <PageTitle>Rail System <span>Configuration</span></PageTitle>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <GuideButton onClick={() => alert("ℹ️ [이동 경로 규칙 안내]\n\n바스켓 이동 순서 결정 기준:\n\n1. 이름 앞의 숫자 (예: 01-A, 02-B)\n2. 물류 키워드 (IB → SR → OB)\n3. 그 외 이름순(가나다)\n\n카드의 번호 순서대로 바스켓이 이동합니다.")}>
            <HelpCircle size={18} />
            규칙 안내
          </GuideButton>
          <div style={{ width: '16px' }} />
          <AddButton onClick={handleAdd}>
            <Plus size={18} />
            새 구획 추가
          </AddButton>
        </div>
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
          {sortedZones.map((zone, index) => (
            <ZoneCard key={zone.id}>
            <StepBadge>{index + 1}</StepBadge>
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
            
            {/* 순번 선택 UI (새 추가 시에만 표시) */}
            {!editingZone && (
              <InputGroup>
                <Label>희망 순번 (자동 선택됨)</Label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Input 
                    type="number" 
                    min="1" 
                    style={{ width: '80px' }}
                    value={parseInt(formData.id.match(/^(\d+)/)?.[1] || '0', 10)}
                    onChange={(e) => {
                      const val = parseInt(e.target.value, 10);
                      if (!isNaN(val) && val > 0) {
                        const prefix = String(val).padStart(2, '0');
                        // 기존 ID에서 숫자 접두어 제거 후 새 접두어 붙이기
                        const suffix = formData.id.replace(/^\d+-?/, '') || '';
                        // suffix가 비어있으면 '-' 붙여줌, 아니면 그대로
                        const newId = suffix ? `${prefix}-${suffix}` : `${prefix}-`;
                        setFormData(prev => ({ ...prev, id: newId }));
                      }
                    }}
                  />
                  <span style={{ fontSize: '13px', color: '#666' }}>번 위치에 삽입 (기존 구획은 뒤로 밀림)</span>
                </div>
              </InputGroup>
            )}

            <InputGroup>
              <Label htmlFor="id">구획 ID (자동 생성)</Label>
              <Input type="text" name="id" value={formData.id} onChange={handleFormChange} required disabled={!!editingZone} placeholder="e.g., 02-PK"/>
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