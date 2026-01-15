import React from 'react';
import styled, { keyframes, css } from 'styled-components';
import { Box } from 'lucide-react'; // Only Box icon needed for the header inside this component

// --- [Animations - Copied from App.js for consistency] ---
const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
`;

// --- [Styled Components - Adapted from App.js for content specific to this dashboard] ---
const RailDashboardContent = styled.div`
  /* This component's main content area will inherit padding and background from App.js's MainContent */
  /* Remove flex: 1 and overflow-y: auto as it's now wrapped by App.js's MainContent */
  /* Remove background-image as it's now handled by App.js's MainContent */
  position: relative;

  /* No scrollbar styles needed here, parent MainContent will handle it */
`;

const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  border-bottom: 1px solid rgba(30, 41, 59, 0.5);
  padding-bottom: 24px;
`;

const HeaderTitleGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 24px;
`;

const HeaderIconBox = styled.div`
  padding: 12px;
  background-color: #0f172a;
  border-radius: 16px;
  border: 1px solid #1e293b;
`;

const TitleText = styled.div`
  h1 {
    font-size: 24px;
    font-weight: 900;
    color: #ffffff;
    font-style: italic;
    letter-spacing: -0.05em;
    margin: 0;
  }
  p {
    font-size: 10px;
    font-weight: 800;
    color: #64748b;
    letter-spacing: 0.4em;
    margin-top: 8px;
  }
`;

const SectionTitle = styled.h2`
  font-size: 20px;
  font-weight: 900;
  color: #ffffff;
  margin-bottom: 24px;
  animation: ${css`${fadeIn} 0.5s ease forwards`};
`;

const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-top: 24px;
  animation: ${fadeIn} 0.5s ease forwards;
`;

const Card = styled.div`
  background-color: rgba(15, 23, 42, 0.8);
  padding: 24px;
  border-radius: 20px;
  border: 1px solid #1e293b;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const CardTitle = styled.h3`
  font-size: 18px;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0;
`;

const CardContent = styled.p`
  font-size: 14px;
  color: #94a3b8;
  line-height: 1.6;
  margin: 0;
`;


const Smart_Logistics_Rail_dashboard = () => {
  return (
    <RailDashboardContent>
      <Header>
        <HeaderTitleGroup>
          <HeaderIconBox><Box size={32} color="#3b82f6" /></HeaderIconBox>
          <TitleText>
            <h1>Rail Logistics <span>DASHBOARD</span></h1>
            <p>REAL-TIME RAILWAY OPERATIONS MONITORING</p>
          </TitleText>
        </HeaderTitleGroup>
        {/* Add other header elements if needed, e.g., LiveIndicator */}
      </Header>

      <SectionTitle>OVERVIEW</SectionTitle>
      <ContentGrid>
        <Card>
          <CardTitle>Total Trains in Transit</CardTitle>
          <CardContent>150 trains are currently active across the network.</CardContent>
        </Card>
        <Card>
          <CardTitle>On-Time Performance</CardTitle>
          <CardContent>92.5% of trains are running on schedule.</CardContent>
        </Card>
        <Card>
          <CardTitle>Critical Alerts</CardTitle>
          <CardContent>3 critical alerts require immediate attention.</CardContent>
        </Card>
      </ContentGrid>

      <SectionTitle style={{ marginTop: '40px' }}>DETAILED STATUS</SectionTitle>
      <ContentGrid>
        <Card>
          <CardTitle>East Route Capacity</CardTitle>
          <CardContent>Current utilization is 78%, approaching peak capacity during rush hours.</CardContent>
        </Card>
        <Card>
          <CardTitle>Maintenance Schedule</CardTitle>
          <CardContent>Next major maintenance for locomotive #456 due in 3 days.</CardContent>
        </Card>
      </ContentGrid>
    </RailDashboardContent>
  );
};

export default Smart_Logistics_Rail_dashboard;
