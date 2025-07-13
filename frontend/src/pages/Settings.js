import React from 'react';

const Settings = () => {
  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Settings</h1>
        <p>Configure your AI platform settings</p>
      </div>
      
      <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
        <h2 style={{ marginBottom: '1rem', color: '#1e293b' }}>Platform Settings</h2>
        <p style={{ color: '#64748b', marginBottom: '2rem' }}>
          Configure API keys, workflow settings, and platform preferences.
        </p>
        <div style={{ 
          background: 'white', 
          padding: '2rem', 
          borderRadius: '1rem', 
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          maxWidth: '600px',
          margin: '0 auto'
        }}>
          <h3 style={{ marginBottom: '1rem', color: '#1e293b' }}>Configuration</h3>
          <p style={{ color: '#64748b' }}>
            Settings for API keys, notifications, and platform configuration will be available here.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Settings; 