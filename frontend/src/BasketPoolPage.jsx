import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import axios from 'axios';

const PageContainer = styled.div`
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
`;

const Header = styled.div`
  background: rgba(255, 255, 255, 0.95);
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const Title = styled.h1`
  margin: 0 0 10px 0;
  color: #333;
  font-size: 28px;
`;

const Stats = styled.div`
  display: flex;
  gap: 20px;
  margin-top: 15px;
`;

const StatBox = styled.div`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 15px 25px;
  border-radius: 8px;
  color: white;
  
  .label {
    font-size: 12px;
    opacity: 0.9;
  }
  
  .value {
    font-size: 24px;
    font-weight: bold;
    margin-top: 5px;
  }
`;

const TableContainer = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  
  thead {
    background: #f8f9fa;
    
    th {
      padding: 12px;
      text-align: left;
      font-weight: 600;
      color: #495057;
      border-bottom: 2px solid #dee2e6;
    }
  }
  
  tbody {
    tr {
      border-bottom: 1px solid #dee2e6;
      transition: background-color 0.2s;
      
      &:hover {
        background-color: #f8f9fa;
      }
      
      td {
        padding: 12px;
        color: #495057;
      }
    }
  }
`;

const StatusBadge = styled.span`
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background-color: ${props => {
    if (props.status === 'assigned') return '#28a745';
    if (props.status === 'in-transit') return '#ffc107';
    return '#6c757d';
  }};
  color: white;
`;

const LoadingText = styled.div`
  text-align: center;
  padding: 40px;
  font-size: 18px;
  color: #6c757d;
`;

const ErrorText = styled.div`
  text-align: center;
  padding: 40px;
  font-size: 18px;
  color: #dc3545;
`;

const BasketPoolPage = () => {
  const [baskets, setBaskets] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [assignedCount, setAssignedCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBaskets();
  }, []);

  const fetchBaskets = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/baskets');
      const { count, baskets: basketList } = response.data;
      
      setTotalCount(count);
      setBaskets(basketList);
      
      // 목적지가 할당된 바스켓 개수 계산
      const assigned = basketList.filter(b => b.destination !== null).length;
      setAssignedCount(assigned);
      
      setError(null);
    } catch (err) {
      console.error('Failed to fetch baskets:', err);
      setError('바스켓 데이터를 가져오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const getBasketStatus = (basket) => {
    if (basket.destination === null) return 'available';
    return 'assigned';
  };

  const getStatusText = (status) => {
    if (status === 'available') return '대기중';
    if (status === 'assigned') return '할당됨';
    return status;
  };

  return (
    <PageContainer>
      <Header>
        <Title>🧺 Basket Pool Management</Title>
        <Stats>
          <StatBox>
            <div className="label">Total Baskets</div>
            <div className="value">{totalCount}</div>
          </StatBox>
          <StatBox>
            <div className="label">Assigned</div>
            <div className="value">{assignedCount}</div>
          </StatBox>
          <StatBox>
            <div className="label">Available</div>
            <div className="value">{totalCount - assignedCount}</div>
          </StatBox>
        </Stats>
      </Header>

      <TableContainer>
        {loading && <LoadingText>Loading baskets...</LoadingText>}
        {error && <ErrorText>{error}</ErrorText>}
        
        {!loading && !error && (
          <Table>
            <thead>
              <tr>
                <th>No.</th>
                <th>Basket ID</th>
                <th>Destination</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {baskets.map((basket, index) => {
                const status = getBasketStatus(basket);
                return (
                  <tr key={basket.basket_id}>
                    <td>{index + 1}</td>
                    <td>{basket.basket_id}</td>
                    <td>{basket.destination || '-'}</td>
                    <td>
                      <StatusBadge status={status}>
                        {getStatusText(status)}
                      </StatusBadge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
        )}
      </TableContainer>
    </PageContainer>
  );
};

export default BasketPoolPage;
