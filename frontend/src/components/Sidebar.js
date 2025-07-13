import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Workflow, 
  BarChart3, 
  Settings,
  Zap,
  Building2
} from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const navItems = [
    {
      path: '/',
      name: 'Dashboard',
      icon: LayoutDashboard
    },
    {
      path: '/workflows',
      name: 'AI Workflows',
      icon: Workflow
    },
    {
      path: '/analytics',
      name: 'Analytics',
      icon: BarChart3
    },
    {
      path: '/settings',
      name: 'Settings',
      icon: Settings
    }
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1>🚀 Aictive</h1>
        <p>AI-Powered Property Management</p>
      </div>
      
      <nav>
        <ul className="nav-menu">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.path} className="nav-item">
                <NavLink
                  to={item.path}
                  className={({ isActive }) => 
                    `nav-link ${isActive ? 'active' : ''}`
                  }
                >
                  <Icon className="nav-icon" />
                  {item.name}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      <div style={{ marginTop: 'auto', padding: '2rem 1rem' }}>
        <div style={{ 
          background: 'rgba(255, 255, 255, 0.1)', 
          borderRadius: '0.5rem', 
          padding: '1rem',
          marginBottom: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
            <Zap size={16} style={{ marginRight: '0.5rem' }} />
            <span style={{ fontSize: '0.875rem', fontWeight: '600' }}>System Status</span>
          </div>
          <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>
            AI Agents: <span style={{ color: '#10b981' }}>Active</span>
          </div>
          <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>
            API: <span style={{ color: '#10b981' }}>Online</span>
          </div>
        </div>

        <div style={{ 
          background: 'rgba(255, 255, 255, 0.1)', 
          borderRadius: '0.5rem', 
          padding: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem' }}>
            <Building2 size={16} style={{ marginRight: '0.5rem' }} />
            <span style={{ fontSize: '0.875rem', fontWeight: '600' }}>Properties</span>
          </div>
          <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>
            Managed: <span style={{ color: '#3b82f6' }}>24</span>
          </div>
          <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>
            Active Issues: <span style={{ color: '#f59e0b' }}>3</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar; 