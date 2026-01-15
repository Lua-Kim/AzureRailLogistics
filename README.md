# AzureRailLogistics Project Documentation

## 1. 프로젝트 개요
이 프로젝트는 물류 센터의 현황을 실시간으로 모니터링하고 분석하는 React 기반의 대시보드 애플리케이션입니다. 전체적인 운영 현황을 파악하는 매크로(Macro) 뷰와 특정 구역의 세부 데이터를 분석하는 마이크로(Micro) 뷰로 구성되어 있습니다.

## 2. 파일 구조 (File Structure)
*   **Root**: `c:\Users\EL0100\Desktop\AzureRailLogistics\`
    *   **frontend\src\**
        *   `DashboardPage.jsx`: 전체 물류 센터의 KPI 및 구역별 상태를 모니터링하는 메인 대시보드 페이지입니다.
        *   `ZoneAnalyticsPage.jsx`: 특정 구역(Zone)의 상세 지표와 센서 데이터를 시각화하는 분석 페이지입니다.

## 3. 주요 기능 및 로직

### A. DashboardPage.jsx (Macro View)
*   **실시간 시뮬레이션**: `useEffect`와 `setInterval`을 사용하여 3초마다 각 구역의 부하(Load), 온도(Temp), 진동(Vib) 데이터를 랜덤하게 변동시키고, 이에 따른 상태(Normal, Warning, Critical)를 갱신합니다.
*   **재생(Playback) 모드**: 과거 데이터를 `history` 배열에 저장하고, 슬라이더를 조작하여 과거 특정 시점의 데이터를 조회할 수 있습니다.
*   **AI 인사이트**: 'ANALYZE' 버튼을 통해 가상의 AI 분석 로직을 실행하고 텍스트 인사이트를 제공합니다.
*   **네비게이션**: 구역 목록(`StatusTable`) 클릭 시 `useNavigate`를 통해 상세 페이지로 이동하며, 해당 구역의 `zoneId`와 `zoneName`을 State로 전달합니다.

### B. ZoneAnalyticsPage.jsx (Micro View)
*   **데이터 수신**: `useLocation` 훅을 사용하여 이전 페이지에서 전달받은 구역 정보를 표시합니다. (데이터 부재 시 기본값 사용)
*   **상세 지표**: TPH(시간당 처리량), 혼잡도, 재순환율, 에너지 효율 등 구체적인 운영 지표를 카드 형태로 표시합니다.
*   **시각화**:
    *   **Trend Chart**: SVG를 활용한 파동 형태의 데이터 트렌드 그래프.
    *   **Sensor Grid**: 랜덤하게 활성화되는 박스 그리드를 통해 센서 데이터 흐름을 시각적으로 표현.

## 4. 기술 스택
*   **Core**: React
*   **Styling**: styled-components
*   **Icons**: lucide-react
*   **Routing**: react-router-dom

## 5. 데이터 흐름 (Data Flow)
1.  **DashboardPage**에서 전체 구역 데이터(`config.zones`)를 관리 및 시뮬레이션합니다.
2.  사용자가 대시보드에서 특정 구역(예: 'PK-01')을 클릭합니다.
3.  **Router**가 화면을 `ZoneAnalyticsPage`로 전환하며, 선택된 구역의 ID와 이름을 전달합니다.
4.  **ZoneAnalyticsPage**는 전달받은 정보를 바탕으로 해당 구역에 특화된 상세 분석 화면을 렌더링합니다.