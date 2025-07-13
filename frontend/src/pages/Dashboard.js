import React, { useState, useEffect } from 'react';
import { 
  Mail, 
  Clock, 
  CheckCircle, 
  AlertTriangle,
  TrendingUp,
  Users,
  Building,
  Activity,
  Workflow,
  BarChart3
} from 'lucide-react';
import axios from 'axios';

const Dashboard = () => {
  const [metrics, setMetrics] = useState({
    emailsProcessed: 0,
    activeWorkflows: 0,
    responseTime: 0,
    accuracy: 0
  });
  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch health status from your API
      const healthResponse = await axios.get('/');
      console.log('API Health:', healthResponse.data);

      // Mock data for now - replace with real API calls
      setMetrics({
        emailsProcessed: 156,
        activeWorkflows: 8,
        responseTime: 2.3,
        accuracy: 94.2
      });

      setRecentActivity([
        {
          id: 1,
          type: 'email_processed',
          title: 'Maintenance Request Processed',
          description: 'Kitchen sink clogged - Unit 2B',
          time: '2 minutes ago',
          status: 'success'
        },
        {
          id: 2,
          type: 'workflow_completed',
          title: 'Response Generated',
          description: 'Professional response sent to tenant',
          time: '5 minutes ago',
          status: 'success'
        },
        {
          id: 3,
          type: 'entity_extracted',
          title: 'Contact Information Extracted',
          description: 'Phone, address, and name identified',
          time: '8 minutes ago',
          status: 'success'
        },
        {
          id: 4,
          type: 'compliance_check',
          title: 'Compliance Verification',
          description: 'Message checked against CA rental laws',
          time: '12 minutes ago',
          status: 'warning'
        }
      ]);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'email_processed':
        return <Mail size={20} />;
      case 'workflow_completed':
        return <CheckCircle size={20} />;
      case 'entity_extracted':
        return <Users size={20} />;
      case 'compliance_check':
        return <AlertTriangle size={20} />;
      default:
        return <Activity size={20} />;
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'success':
        return 'status-success';
      case 'warning':
        return 'status-warning';
      case 'error':
        return 'status-error';
      default:
        return 'status-info';
    }
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div style={{ fontSize: '1.5rem', color: '#64748b' }}>Loading Dashboard...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Command Center Dashboard</h1>
        <p>Real-time monitoring of your AI-powered property management system</p>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Emails Processed</span>
            <Mail className="metric-icon" />
          </div>
          <div className="metric-value">{metrics.emailsProcessed}</div>
          <div className="metric-change">+12% from last week</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Active Workflows</span>
            <Clock className="metric-icon" />
          </div>
          <div className="metric-value">{metrics.activeWorkflows}</div>
          <div className="metric-change">3 in progress</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Avg Response Time</span>
            <TrendingUp className="metric-icon" />
          </div>
          <div className="metric-value">{metrics.responseTime}s</div>
          <div className="metric-change">-0.5s from last week</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">AI Accuracy</span>
            <CheckCircle className="metric-icon" />
          </div>
          <div className="metric-value">{metrics.accuracy}%</div>
          <div className="metric-change">+2.1% from last week</div>
        </div>
      </div>

      <div className="content-grid">
        <div className="recent-activity">
          <h2>Recent AI Activity</h2>
          {recentActivity.map((activity) => (
            <div key={activity.id} className="activity-item">
              <div className="activity-icon">
                {getActivityIcon(activity.type)}
              </div>
              <div className="activity-content">
                <h4>{activity.title}</h4>
                <p>{activity.description}</p>
              </div>
              <div className="activity-time">
                <span className={`status-badge ${getStatusClass(activity.status)}`}>
                  {activity.status}
                </span>
                <div style={{ marginTop: '0.25rem' }}>{activity.time}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="quick-actions">
          <h2>Quick Actions</h2>
          <div className="action-buttons">
            <a href="/workflows" className="action-button">
              <Workflow className="action-button-icon" />
              Test AI Workflow
            </a>
            <a href="/analytics" className="action-button">
              <BarChart3 className="action-button-icon" />
              View Analytics
            </a>
            <button className="action-button" onClick={() => window.open('http://localhost:8000/docs', '_blank')}>
              <Activity className="action-button-icon" />
              API Documentation
            </button>
            <button className="action-button" onClick={() => window.open('http://localhost:8000', '_blank')}>
              <Building className="action-button-icon" />
              Health Check
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 