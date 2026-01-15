import React from 'react';
import styled from 'styled-components';

const SettingsPageContainer = styled.div`
  padding: 40px;
  color: ${props => props.theme.colors.text.main};
  background-color: ${props => props.theme.colors.surfaceTransparent};
  border-radius: 20px;
  border: 1px solid ${props => props.theme.colors.border};
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 200px;
`;

const PageTitle = styled.h2`
  font-size: 24px;
  font-weight: 900;
  margin-bottom: 20px;
`;

const PageContent = styled.p`
  font-size: 16px;
  color: ${props => props.theme.colors.text.sub};
`;

const DataSettingPage = () => {
  return (
    <SettingsPageContainer>
      <PageTitle>Data Setting</PageTitle>
      <PageContent>This is a placeholder for the Data Setting.</PageContent>
      <PageContent>You can add various configuration options here.</PageContent>
    </SettingsPageContainer>
  );
};

export default DataSettingPage;
