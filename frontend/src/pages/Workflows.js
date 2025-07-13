import React from 'react';

const Workflows = () => {
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>AI Workflows</h1>
        <p>Test and manage your AI-powered workflows</p>
      </div>
      
      <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
        <h2 style={{ marginBottom: '1rem', color: '#1e293b' }}>Workflow Management</h2>
        <p style={{ color: '#64748b', marginBottom: '2rem' }}>
          This page will allow you to test and manage AI workflows.
        </p>
        <button 
          onClick={() => window.open('http://localhost:8000/docs', '_blank')}
          style={{
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            padding: '0.75rem 1.5rem',
            borderRadius: '0.5rem',
            fontSize: '1rem',
            cursor: 'pointer'
          }}
        >
          Open API Documentation
        </button>
      </div>
    </div>
  );
};

export default Workflows; 