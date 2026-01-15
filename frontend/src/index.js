import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import SmartLogisticsDashboard from './App'; // App.js now exports SmartLogisticsDashboard

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <SmartLogisticsDashboard />
  </React.StrictMode>
);

