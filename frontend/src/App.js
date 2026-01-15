// --- [Imports] ---
import React, { useState, useEffect } from 'react';
import styled, { keyframes, css, ThemeProvider } from 'styled-components';
import { BrowserRouter as Router, Routes, Route, NavLink, Navigate, useLocation } from 'react-router-dom';
import { 
  Layout, Database, Activity, Box, Server, Sun, Moon, Laptop
} from 'lucide-react';

// Custom Components
import LogisticsManagementPage from './Logistics_management';
import ZoneAnalyticsPage from './ZoneAnalyticsPage';
import DashboardPage from './DashboardPage';
import LogisticsRailSettingPage from './LogisticsRailSettingPage'; 
import DataSettingPage from './DataSettingPage';

// Styles
import { lightTheme, darkTheme } from './theme';
import GlobalStyle from './GlobalStyle';

// --- [Animations] ---
const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
`;

// --- [Styled Components] ---

// 최상위 레이아웃 컨테이너: 전체 애플리케이션의 배경과 기본 레이아웃을 정의합니다.
const Container = styled.div`
  min-height: 100vh;
  background-color: ${props => props.theme.colors.background};
  color: ${props => props.theme.colors.text.main};
  font-family: ${props => props.theme.fonts.main};
  display: flex;
  overflow: hidden;
  transition: all 0.5s ease;

  ${props => props.isFullscreen && css`
    position: fixed;
    inset: 0;
    z-index: 9999;
  `}
`;

// 사이드바: 메인 내비게이션 영역을 담당합니다.
const Sidebar = styled.nav`
  width: 96px;
  background-color: ${props => props.theme.colors.surface};
  border-right: 1px solid ${props => props.theme.colors.border};
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
  gap: 32px;
  flex-shrink: 0;
  z-index: 100;
`;

// 내비게이션 버튼: 각 페이지로 이동하는 버튼입니다. active prop에 따라 스타일이 변경됩니다.
const StyledNavLink = styled(NavLink)`
  padding: 16px;
  border-radius: ${props => props.theme.borderRadius};
  background: transparent;
  border: 1px solid transparent;
  color: ${props => props.theme.colors.text.muted};
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    color: ${props => props.theme.colors.text.sub};
    background-color: ${props => props.theme.colors.surface};
  }

  &.active {
    background-color: ${props => props.theme.colors.surface};
    color: ${props => props.theme.colors.primary};
    border-color: ${props => props.theme.colors.border};
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
  }
`;

const ThemeToggleButton = styled.button`
  margin-top: auto;
  padding: 16px;
  border-radius: ${props => props.theme.borderRadius};
  background: transparent;
  border: 1px solid transparent;
  color: ${props => props.theme.colors.text.muted};
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    color: ${props => props.theme.colors.text.sub};
    background-color: ${props => props.theme.colors.surface};
  }
`;

// 메인 콘텐츠 영역: 선택된 탭의 내용을 표시하는 주요 영역입니다.
const MainContent = styled.main`
  flex: 1;
  overflow-y: auto;
  padding: 40px;
  background-image: 
    radial-gradient(circle at top right, ${props => props.theme.colors.surfaceHighlight} 0%, transparent 45%),
    radial-gradient(circle at bottom left, ${props => props.theme.colors.surface} 0%, transparent 45%);
  position: relative;
`;

// 헤더: 메인 콘텐츠 상단에 표시되는 제목 및 실시간 상태 표시 영역입니다.
const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${props => props.$compact ? '16px' : '32px'};
  border-bottom: 1px solid ${props => props.theme.colors.border};
  padding-bottom: ${props => props.$compact ? '12px' : '24px'};
  transition: all 0.3s ease;
`;

// 헤더의 제목 그룹: 아이콘과 텍스트 제목을 포함합니다.
const HeaderTitleGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 24px;
`;

// 헤더 아이콘 박스: 제목 옆에 표시되는 아이콘을 감싸는 컨테이너입니다.
const HeaderIconBox = styled.div`
  padding: ${props => props.$compact ? '6px' : '12px'};
  background-color: ${props => props.theme.colors.surface};
  border-radius: ${props => props.theme.borderRadius};
  border: 1px solid ${props => props.theme.colors.border};
  transition: all 0.3s ease;
`;

// 헤더의 텍스트 제목: 대시보드의 주 제목과 부제목을 표시합니다.
const TitleText = styled.div`
  h1 {
    font-size: ${props => props.$compact ? '14px' : '24px'};
    font-weight: 900;
    color: ${props => props.theme.colors.text.inverse};
    font-style: italic;
    letter-spacing: -0.05em;
    margin: 0;
    transition: all 0.3s ease;
  }
  p {
    font-size: ${props => props.$compact ? '8px' : '10px'};
    font-weight: 800;
    color: ${props => props.theme.colors.text.muted};
    letter-spacing: 0.4em;
    margin-top: ${props => props.$compact ? '4px' : '8px'};
    transition: all 0.3s ease;
  }
`;

// 실시간 상태 표시기: 'PIPELINE: LIVE'와 같은 실시간 상태를 나타냅니다.
const LiveIndicator = styled.div`
  background-color: ${props => props.theme.colors.surface};
  padding: 12px 24px;
  border-radius: ${props => props.theme.borderRadius};
  border: 1px solid ${props => props.theme.colors.border};
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.1em;
  color: ${props => props.theme.colors.text.sub};

  &::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: ${props => props.theme.colors.status.live};
    box-shadow: 0 0 10px ${props => props.theme.colors.status.live};
  }
`;

// --- [Main Component] ---
const AppContent = ({ themeMode, toggleTheme }) => {
  const location = useLocation();
  const isDashboard = location.pathname === '/dashboard' || location.pathname === '/';
  const isCompact = !isDashboard;
  // 전체 화면 모드 활성화 여부를 관리하는 상태
  const [isPseudoFullscreen, setIsPseudoFullscreen] = useState(false);

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
      <Container isFullscreen={isPseudoFullscreen}>
        {/* 사이드바 영역 */}
        <Sidebar>
          
          {/* 내비게이션 버튼들 */}
          <StyledNavLink to="/dashboard"><Layout size={24}/></StyledNavLink>
          <StyledNavLink to="/zone_analytics"><Activity size={24}/></StyledNavLink>
          <StyledNavLink to="/logistis_management"><Server size={24}/></StyledNavLink>
          <StyledNavLink to="/logistis_rail_setting"><Box size={24}/></StyledNavLink>
          <StyledNavLink to="/data_setting"><Database size={24}/></StyledNavLink>

          <ThemeToggleButton onClick={toggleTheme}>
            {renderThemeIcon()}
          </ThemeToggleButton>
        </Sidebar>

        {/* 메인 콘텐츠 영역 */}
        <MainContent>
          {/* Header will be static now */}
          <Header $compact={isCompact}>
            <HeaderTitleGroup>
              <HeaderIconBox $compact={isCompact}><Box size={isCompact ? 20 : 32} color="#3b82f6" /></HeaderIconBox>
              <TitleText $compact={isCompact}>
                <h1>SROC <span>PORTAL</span></h1>
                <p>INTEGRATED OPERATIONAL TOPOLOGY HUB</p>
              </TitleText>
            </HeaderTitleGroup>
            <LiveIndicator>PIPELINE: LIVE</LiveIndicator>
          </Header>

          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/zone_analytics" element={<ZoneAnalyticsPage />} />
            <Route path="/logistis_management" element={<LogisticsManagementPage />} />
            <Route path="/logistis_rail_setting" element={<LogisticsRailSettingPage />} />
            <Route path="/data_setting" element={<DataSettingPage />} />
          </Routes>
        </MainContent>
      </Container>
  );
};

const SmartLogisticsDashboard = () => {
  const [themeMode, setThemeMode] = useState('dark'); // dark, light, system
  const [activeTheme, setActiveTheme] = useState(darkTheme);

  useEffect(() => {
    if (themeMode === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      setActiveTheme(mediaQuery.matches ? darkTheme : lightTheme);

      const handler = (e) => setActiveTheme(e.matches ? darkTheme : lightTheme);
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    } else {
      setActiveTheme(themeMode === 'dark' ? darkTheme : lightTheme);
    }
  }, [themeMode]);

  const toggleTheme = () => {
    setThemeMode(prevMode => {
      if (prevMode === 'dark') return 'light';
      if (prevMode === 'light') return 'system';
      return 'dark';
    });
  };

  return (
    // 전체 애플리케이션의 렌더링 시작
    <ThemeProvider theme={activeTheme}>
    <GlobalStyle />
    <Router>
      <AppContent themeMode={themeMode} toggleTheme={toggleTheme} />
    </Router>
    </ThemeProvider>
  );
};

export default SmartLogisticsDashboard;