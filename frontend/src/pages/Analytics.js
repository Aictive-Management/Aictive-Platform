import React from 'react';

const Analytics = () => {
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Analytics</h1>
        <p>AI performance metrics and insights</p>
      </div>
      
      <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
        <h2 style={{ marginBottom: '1rem', color: '#1e293b' }}>Analytics Dashboard</h2>
        <p style={{ color: '#64748b', marginBottom: '2rem' }}>
          This page will show detailed analytics and performance metrics.
        </p>
        <div style={{ 
          background: 'white', 
          padding: '2rem', 
          borderRadius: '1rem', 
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          maxWidth: '600px',
          margin: '0 auto'
        }}>
          <h3 style={{ marginBottom: '1rem', color: '#1e293b' }}>Coming Soon</h3>
          <p style={{ color: '#64748b' }}>
            Advanced analytics with charts, performance tracking, and insights will be available here.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Analytics; 