import { createGlobalStyle } from 'styled-components';

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }



  body {
    background-color: ${props => props.theme.colors.background};
    color: ${props => props.theme.colors.text.main};
    font-family: ${props => props.theme.fonts.main};
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  #root {
    height: 100%;
    width: 100%;
  }
  /* 전체 페이지 스크롤 방지 */
  html, body {
    margin: 0;
    padding: 0;
    height: 100%;
    overflow: hidden; /* 이 부분이 핵심입니다. 중복 스크롤을 없앱니다. */
  }

  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: ${props => props.theme.colors.border};
    border-radius: 3px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: ${props => props.theme.colors.text.muted};
  }
`;

export default GlobalStyle;