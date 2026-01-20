import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Activity, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import axios from 'axios';

const PageContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 20px;
  import React, { useState } from 'react';
  import axios from 'axios';


  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const RealtimeMonitoringPage = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);

    const handleStart = async () => {
      setLoading(true);
      let newLogs = [];
      try {
        // 바스켓 데이터
        const basketsRes = await axios.get(`${API_BASE_URL}/baskets`);
        newLogs.push('=== /baskets 응답 ===');
        newLogs.push(JSON.stringify(basketsRes.data, null, 2));

        // 이벤트 데이터
        const eventsRes = await axios.get(`${API_BASE_URL}/events/latest?count=20`);
        newLogs.push('=== /events/latest 응답 ===');
        newLogs.push(JSON.stringify(eventsRes.data, null, 2));

        // 존 데이터
        const zonesRes = await axios.get(`${API_BASE_URL}/zones`);
        newLogs.push('=== /zones 응답 ===');
        newLogs.push(JSON.stringify(zonesRes.data, null, 2));

        setLogs(newLogs);
      } catch (err) {
        newLogs.push('에러 발생: ' + (err.message || err));
        setLogs(newLogs);
      } finally {
        setLoading(false);
      }
    };

    return (
      <div style={{ padding: 24, background: '#18181b', minHeight: '100vh', color: '#e5e7eb', fontFamily: 'monospace' }}>
        <h2 style={{ fontWeight: 900, fontSize: 22, marginBottom: 16 }}>디버깅 로그 뷰어</h2>
        <button onClick={handleStart} disabled={loading} style={{ padding: '10px 24px', fontWeight: 700, fontSize: 16, borderRadius: 8, border: 'none', background: '#3b82f6', color: 'white', cursor: 'pointer', marginBottom: 24 }}>
          {loading ? '로딩 중...' : '시작'}
        </button>
        <div style={{ background: '#23272e', borderRadius: 8, padding: 16, minHeight: 300, whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.6, maxHeight: 600, overflowY: 'auto' }}>
          {logs.length === 0 ? '아직 로그가 없습니다.' : logs.map((line, idx) => <div key={idx}>{line}</div>)}
        </div>
      </div>
    );
  };

  export default RealtimeMonitoringPage;
        // 존 데이터 처리
        const zones = zonesRes.data || (Array.isArray(zonesRes.data) ? zonesRes.data : []);
        const totalSensors = zones.reduce((sum, zone) => sum + (zone.sensors || 0), 0);

        setStats({
          totalBaskets: baskets.length,
          movingBaskets: movingBaskets,
          totalSensors: totalSensors,
          activeSignals: activeSignals,
          zones: zones,
          recentEvents: events,
        });

        setLastUpdate(new Date());
        setError(null);
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000); // 3초마다 갱신

    return () => clearInterval(interval);
  }, []);

  const zoneStats = stats.zones.map((zone, idx) => ({
    name: zone.zone_id || `Zone ${idx + 1}`,
    sensors: zone.sensors || 0,
    lines: zone.lines || 0,
  }));

  const handleSimulatorToggle = async () => {
    try {
      const endpoint = simulatorActive ? '/simulator/stop' : '/simulator/start';
      await axios.post(`${API_BASE_URL}${endpoint}`);
      setSimulatorActive(!simulatorActive);
    } catch (err) {
      console.error('시뮬레이터 제어 실패:', err);
    }
  };

  return (
    <PageContainer>
      <Header>
        <Title>
          <Activity size={28} />
          실시간 모니터링
        </Title>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            onClick={handleSimulatorToggle}
            style={{
              padding: '8px 16px',
              backgroundColor: simulatorActive ? '#ef4444' : '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 700,
              transition: 'all 0.3s ease',
            }}
          >
            {simulatorActive ? '시뮬레이터 중지' : '시뮬레이터 시작'}
          </button>
          <StatusBadge isActive={simulatorActive}>
            {simulatorActive ? '라이브 스트리밍' : '대기 중'}
          </StatusBadge>
        </div>
      </Header>

      {error && (
        <Card style={{ backgroundColor: '#ef444420', borderColor: '#ef4444' }}>
          <CardTitle>오류</CardTitle>
          <CardValue style={{ color: '#ef4444', fontSize: '14px' }}>
            {error}
          </CardValue>
        </Card>
      )}

      <Grid>
        <Card>
          <CardTitle>총 바스켓</CardTitle>
          <CardValue>{stats.totalBaskets}</CardValue>
          <CardSubtext>
            <TrendingUp size={14} />
            {stats.movingBaskets}개 이동 중
          </CardSubtext>
        </Card>

        <Card>
          <CardTitle>활성 센서</CardTitle>
          <CardValue>{stats.activeSignals}</CardValue>
          <CardSubtext>
            <CheckCircle size={14} />
            총 {stats.totalSensors}개 센서
          </CardSubtext>
        </Card>

        <Card>
          <CardTitle>존 구역</CardTitle>
          <CardValue>{stats.zones.length}</CardValue>
          <CardSubtext>
            운영 중인 물류센터 구역
          </CardSubtext>
        </Card>

        <Card>
          <CardTitle>신호 감지율</CardTitle>
          <CardValue>
            {stats.totalSensors > 0 ? Math.round((stats.activeSignals / stats.totalSensors) * 100) : 0}%
          </CardValue>
          <CardSubtext>
            마지막 업데이트: {lastUpdate.toLocaleTimeString()}
          </CardSubtext>
        </Card>
      </Grid>

      {zoneStats.length > 0 && (
        <ChartContainer>
          <ChartTitle>존별 센서 분포</ChartTitle>
          <BarChart>
            {zoneStats.map((zone, idx) => (
              <Bar 
                key={idx} 
                height={(zone.sensors / Math.max(...zoneStats.map(z => z.sensors))) * 100}
                value={zone.sensors}
              />
            ))}
          </BarChart>
          <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: '30px', fontSize: '12px' }}>
            {zoneStats.map((zone, idx) => (
              <div key={idx} style={{ textAlign: 'center', color: '#888' }}>
                {zone.name}
              </div>
            ))}
          </div>
        </ChartContainer>
      )}

      <Table>
        <TableHeader>
          <div>존</div>
          <div>센서 ID</div>
          <div>신호</div>
          <div>방향</div>
          <div>시간</div>
        </TableHeader>
        {stats.recentEvents.slice(0, 15).map((event, idx) => (
          <TableRow key={idx}>
            <ZoneBadge>{event.zone_id || '-'}</ZoneBadge>
            <SensorValue title={event.sensor_id}>{event.sensor_id?.substring(0, 20) || '-'}</SensorValue>
            <SignalBadge signal={event.signal}>
              {event.signal ? '활성' : '비활성'}
            </SignalBadge>
            <SensorValue>{event.direction || 'STOP'}</SensorValue>
            <SensorValue>
              {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : '미정'}
            </SensorValue>
          </TableRow>
        ))}
      </Table>

      {stats.recentEvents.length === 0 && !isLoading && (
        <Card style={{ textAlign: 'center' }}>
          <CardSubtext>아직 센서 이벤트가 없습니다</CardSubtext>
        </Card>
      )}
    </PageContainer>
  );
};

export default RealtimeMonitoringPage;
