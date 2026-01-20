import React, { useEffect, useState } from 'react';

function VisualizationDebugPage() {
  const [zones, setZones] = useState([]);
  const [lines, setLines] = useState([]);
  const [baskets, setBaskets] = useState([]);
  const [movements, setMovements] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(0);
  const [statusText, setStatusText] = useState("");

  useEffect(() => {
    async function fetchAll() {
      setLoading(true);
      setError(null);
      try {
        // 존 정보
        const zonesRes = await fetch('http://localhost:8000/zones');
        const zonesData = await zonesRes.json();
        setZones(zonesData);

        // 라인 정보 (존별로 합침)
        let allLines = [];
        zonesData.forEach(z => {
          if (z.zone_lines) allLines = allLines.concat(z.zone_lines);
        });
        setLines(allLines);

        // 바스켓 정보
        const basketsRes = await fetch('http://localhost:8000/baskets');
        const basketsData = await basketsRes.json();
        setBaskets(basketsData);

        // 바스켓 무브먼트(이동) 정보
        const moveRes = await fetch('http://localhost:8000/baskets/movements');
        const moveData = await moveRes.json();
        setMovements(moveData);

        // 모든 센서 이벤트 정보 (최대 10000개)
        console.log('fetching events...');
        const response = await fetch('http://localhost:8000/events/latest?count=10000');
        setStatus(response.status);
        setStatusText(response.statusText);
        console.log("Response status:", response.status, response.statusText);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        // 백엔드가 {events: [...], count: N} 형태로 반환하므로 events 필드 사용
        if (Array.isArray(data)) {
          setEvents(data);
        } else if (Array.isArray(data.events)) {
          setEvents(data.events);
        } else {
          setEvents([]);
        }
        console.log("Fetched events:", data);
      } catch (e) {
        setError(e.message);
        console.error('fetch error', e);
      }
      setLoading(false);
    }
    fetchAll();
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <h2>Visualization Debug Page</h2>
      <div style={{ marginBottom: 8 }}>
        <strong>HTTP status:</strong> {status} {statusText}
      </div>
      {loading && <div>Loading...</div>}
      {error && <div style={{ color: 'red' }}>Error: {error}</div>}
      <div>이벤트 개수: {events.length}</div>
      <h3>Zones</h3>
      <pre>{JSON.stringify(zones, null, 2)}</pre>
      <h3>Lines</h3>
      <pre>{JSON.stringify(lines, null, 2)}</pre>
      <h3>Baskets</h3>
      <pre>{JSON.stringify(baskets, null, 2)}</pre>
      <h3>Basket Movements</h3>
      <pre>{JSON.stringify(movements, null, 2)}</pre>
      <h3>All Sensor Events (최대 10000개)</h3>
      <pre>{JSON.stringify(events, null, 2)}</pre>
    </div>
  );
}

export default VisualizationDebugPage;
