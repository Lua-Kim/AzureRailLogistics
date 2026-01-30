
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import styled, { ThemeProvider } from 'styled-components';
import { Truck, Box, Activity, Sun, Moon, Laptop, Home, Play, Pause } from 'lucide-react';
import axios from 'axios';
import LogisticsRailSettingPage from './LogisticsRailSettingPage';
import BasketVisualizationPage from './BasketVisualizationPage';
import VisualizationDebugPage from './VisualizationDebugPage';

// --- [Styled Components] ---
const Container = styled.div`
  display: flex;
  height: 100vh;
  background-color: ${props => props.theme.colors.background};
  color: ${props => props.theme.colors.text.main};
  transition: background-color 0.3s ease;
`;

const Sidebar = styled.div`
  width: 70px;
  background-color: ${props => props.theme.colors.surface};
  border-right: 1px solid ${props => props.theme.colors.border};
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 0;
  gap: 24px;
  z-index: 10;
`;

const MainContent = styled.div`
  flex: 1;
  overflow-y: auto;
  position: relative;
`;

const SimulatorSwitch = styled.button`
  position: fixed;
  top: 6px;
  right: 17px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background-color: ${props => props.$isRunning 
    ? 'rgba(16, 185, 129, 0.1)' 
    : 'rgba(239, 68, 68, 0.1)'};
  color: ${props => props.$isRunning ? '#059669' : '#dc2626'};
  border: none;
  border-radius: 0;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1000;
  box-shadow: none;

  &:hover {
    background-color: ${props => props.$isRunning 
      ? 'rgba(16, 185, 129, 0.2)' 
      : 'rgba(239, 68, 68, 0.2)'};
    transform: scale(1.05);
  }

  svg {
    width: 14px;
    height: 14px;
  }
`;

const StyledNavLink = styled(NavLink)`
  color: ${props => props.theme.colors.text.sub};
  padding: 12px;
  border-radius: 12px;
  transition: all 0.2s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  
  &:hover {
    background-color: ${props => props.theme.colors.surfaceHighlight};
    color: ${props => props.theme.colors.primary};
  }
  
  &.active {
    background-color: ${props => props.theme.colors.primary};
    color: white;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  }
`;

const ThemeToggleButton = styled.button`
  margin-top: auto;
  background: none;
  border: none;
  color: ${props => props.theme.colors.text.sub};
  cursor: pointer;
  padding: 10px;
  border-radius: 50%;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: ${props => props.theme.colors.surfaceHighlight};
    color: ${props => props.theme.colors.text.main};
  }
`;

const lightTheme = {
  colors: { background: '#f8f9fa', surface: '#ffffff', surfaceHighlight: '#f1f3f5', border: '#e9ecef', primary: '#3b82f6', text: { main: '#212529', sub: '#868e96', muted: '#adb5bd' }, status: { success: '#10b981', warning: '#f59e0b', danger: '#ef4444' } },
  borderRadius: '12px'
};

const darkTheme = {
  colors: { background: '#121212', surface: '#1e1e1e', surfaceHighlight: '#2c2c2c', border: '#333333', primary: '#3b82f6', text: { main: '#e0e0e0', sub: '#a0a0a0', muted: '#606060' }, status: { success: '#10b981', warning: '#f59e0b', danger: '#ef4444' } },
  borderRadius: '12px'
};

// --- [Components] ---
const Dashboard = () => (
  <div style={{ padding: '40px' }}>
    <h1 style={{ fontSize: '32px', fontWeight: '900', marginBottom: '16px' }}>Azure Rail Logistics</h1>
    <p style={{ fontSize: '16px', lineHeight: '1.6', opacity: 0.7 }}>
      물류 센터 레일 트래픽 시뮬레이션 시스템입니다.<br/>
      좌측 메뉴를 선택하여 작업을 시작하세요.
    </p>
  </div>
);

const App = () => {
  const [themeMode, setThemeMode] = useState('dark');
  const [simulatorRunning, setSimulatorRunning] = useState(true);
  const theme = themeMode === 'light' ? lightTheme : darkTheme;
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // 초기 로드 시 시뮬레이터 상태 확인
  useEffect(() => {
    const checkSimulatorStatus = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/simulator/status`);
        if (res.data) {
          setSimulatorRunning(res.data.running);
        }
      } catch (err) {
        console.error('시뮬레이터 상태 확인 실패:', err);
      }
    };
    checkSimulatorStatus();
  }, [API_BASE_URL]);

  const handleSimulatorSwitch = async () => {
    try {
      const endpoint = simulatorRunning ? '/simulator/stop' : '/simulator/start';
      await axios.post(`${API_BASE_URL}${endpoint}`);
      setSimulatorRunning(!simulatorRunning);
    } catch (error) {
      console.error('시뮬레이터 제어 실패:', error);
      alert('시뮬레이터 제어 중 오류가 발생했습니다.');
    }
  };

  const toggleTheme = () => {
    setThemeMode(prev => prev === 'light' ? 'dark' : 'light');
  };

  const renderThemeIcon = () => {
    switch (themeMode) {
      case 'light':
        return <Sun size={24} />;
      case 'dark':
        return <Moon size={24} />;
      default:
        return <Laptop size={24} />;
    }
  };

  return (
    <Router>
      <ThemeProvider theme={theme}>
        <Container isFullscreen={false}>
          {/* 사이드바 영역 */}
          <Sidebar>
            
            {/* 내비게이션 버튼들 */}
            <StyledNavLink to="/" title="홈" end><Home size={24}/></StyledNavLink>
            <StyledNavLink to="/visualization" title="바스켓 시각화"><Truck size={24}/></StyledNavLink>
            <StyledNavLink to="/logistics_rail_setting" title="레일 설정"><Box size={24}/></StyledNavLink>
            <StyledNavLink to="/visualization_debug" title="디버그"><Activity size={24}/></StyledNavLink>

            <ThemeToggleButton onClick={toggleTheme}>
              {renderThemeIcon()}
            </ThemeToggleButton>
          </Sidebar>

          {/* 메인 콘텐츠 영역 */}
          <MainContent>
            {/* Header will be static now */}
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/logistics_rail_setting" element={<LogisticsRailSettingPage />} />
              <Route path="/visualization" element={<BasketVisualizationPage />} />
              <Route path="/visualization_debug" element={<VisualizationDebugPage />} />
              <Route path="*" element={<div style={{ padding: '24px' }}>페이지를 준비 중입니다.</div>} />
            </Routes>
          </MainContent>

          <SimulatorSwitch $isRunning={simulatorRunning} onClick={handleSimulatorSwitch}>
            {simulatorRunning ? <Play size={14} /> : <Pause size={14} />}
            {simulatorRunning ? '실행중' : '중지'}
          </SimulatorSwitch>
        </Container>
      </ThemeProvider>
    </Router>
  );
};

export default App;
